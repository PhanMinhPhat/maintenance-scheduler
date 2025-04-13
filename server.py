from flask import Flask, request, jsonify, send_from_directory, send_file, make_response
from flask_cors import CORS
import pandas as pd
import torch
from datetime import datetime, timedelta
import os
import numpy as np
import logging

from models.maintenance_env import MaintenanceEnv
from models.dqn_agent import MaintenanceAgent
from utils.data_generator import MaintenanceDataGenerator

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app, resources={r"/api/*": {"origins": ["http://localhost:8081", "http://localhost:8083", "http://localhost:5000"]}})

# Initialize the model and agent
def load_model():
    # Load sample data for state space initialization
    data_gen = MaintenanceDataGenerator(num_machines=1)
    equipment_df, history_df, issues_df = data_gen.generate_all_data()
    
    # Initialize environment
    env = MaintenanceEnv(equipment_df, history_df, issues_df)
    state_size = env.observation_space.shape[0]
    action_size = env.action_space.n
    
    # Initialize and load trained agent
    agent = MaintenanceAgent(state_size, action_size)
    agent.load('models/saved/maintenance_dqn_best.pth')
    
    return env, agent

# Serve UI5 static files
@app.route('/')
def serve_ui():
    return send_from_directory('ui/webapp', 'index.html')

@app.route('/<path:path>')
def serve_static(path):
    return send_from_directory('ui/webapp', path)

@app.route('/api/generate_schedule', methods=['POST'])
def generate_schedule():
    try:
        # Get equipment data
        equipment_df = pd.read_csv('data/sample_data/equipment_master.csv', index_col='equipment_id')
        history_df = pd.read_csv('data/sample_data/maintenance_history.csv')
        current_issues = pd.read_csv('data/uploads/current_issues.csv')
        
        # Initialize environment and load agent
        env = MaintenanceEnv(equipment_df, history_df)
        agent = MaintenanceAgent(state_size=8, action_size=2)
        agent.load('models/saved/maintenance_dqn_best.pth')
        
        schedule = []
        current_date = datetime.now()
        
        for _, equipment in env.equipment_df.iterrows():
            # Get equipment state
            env.current_equipment = equipment
            env.current_date = current_date
            state = env._get_state()
            
            # Get maintenance decision and probability
            actions, probs = agent.predict_maintenance(state.reshape(1, -1))
            maintenance_needed = actions[0] == 1
            confidence = probs[0][1]  # Probability of maintenance action
            
            if maintenance_needed:
                # Get current issues for this equipment
                equipment_issues = current_issues[current_issues['equipment_id'] == equipment.name]
                highest_priority = int(equipment_issues['priority'].min()) if not equipment_issues.empty else 4
                
                # Determine maintenance type based on issue type and priority
                issue_types = equipment_issues['notification_type'].unique() if not equipment_issues.empty else []
                if 'HYDR' in issue_types or highest_priority == 1:
                    maint_type = 'PM03'  # Emergency maintenance for hydraulic issues or priority 1
                elif 'MECH' in issue_types or 'ELEC' in issue_types or highest_priority == 2:
                    maint_type = 'PM02'  # Corrective maintenance for mechanical/electrical issues or priority 2
                else:
                    maint_type = 'PM01'  # Preventive maintenance for other cases
                
                # Calculate days until maintenance based on priority
                if highest_priority == 1:
                    days_until_maintenance = 1  # Next day for critical issues
                elif highest_priority == 2:
                    days_until_maintenance = max(2, min(3, int(5 * (1 - confidence))))  # 2-3 days for high priority
                elif highest_priority == 3:
                    days_until_maintenance = max(7, min(14, int(14 * (1 - confidence))))  # 1-2 weeks for medium priority
                else:
                    days_until_maintenance = max(14, min(30, int(30 * (1 - confidence))))  # 2-4 weeks for low priority
                
                # Map priority to text
                priority_map = {1: 'Critical', 2: 'High', 3: 'Medium', 4: 'Low'}
                priority = priority_map.get(highest_priority, 'Low')
                
                schedule.append({
                    'equipment_id': equipment.name,
                    'equipment_type': equipment['equipment_type'],
                    'functional_location': equipment['functional_location'],
                    'manufacturer': equipment['manufacturer'],
                    'suggested_date': (current_date + timedelta(days=days_until_maintenance)).strftime('%Y-%m-%d'),
                    'maintenance_type': maint_type,
                    'priority': priority,
                    'confidence': float(confidence),
                    'breakdown_risk': float(state[5]),
                    'estimated_duration': float(env._estimate_maintenance_cost() / 100)  # Rough estimate in hours
                })
        
        return jsonify(schedule)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/upload_issues', methods=['POST'])
def upload_issues():
    try:
        logger.debug("Starting upload_issues process")
        # Save uploaded file
        file = request.files['file']
        if not file:
            logger.error("No file uploaded")
            return jsonify({'error': 'No file uploaded'}), 400
            
        uploads_dir = os.path.join('data', 'uploads')
        if not os.path.exists(uploads_dir):
            os.makedirs(uploads_dir)
            
        file_path = os.path.join(uploads_dir, 'current_issues.csv')
        file.save(file_path)
        logger.debug(f"File saved to {file_path}")
        
        # Load data
        logger.debug("Loading data files")
        try:
            # Load equipment data without setting index
            equipment_df = pd.read_csv('data/sample_data/equipment_master.csv')
            logger.debug(f"Equipment data loaded, shape: {equipment_df.shape}")
        except Exception as e:
            logger.error(f"Error loading equipment data: {str(e)}")
            raise
            
        try:
            history_df = pd.read_csv('data/sample_data/maintenance_history.csv')
            logger.debug(f"History data loaded, shape: {history_df.shape}")
        except Exception as e:
            logger.error(f"Error loading history data: {str(e)}")
            raise
            
        try:
            current_issues = pd.read_csv(file_path)
            logger.debug(f"Current issues loaded, shape: {current_issues.shape}")
            logger.debug(f"Current issues columns: {current_issues.columns.tolist()}")
        except Exception as e:
            logger.error(f"Error loading current issues: {str(e)}")
            raise
        
        # Initialize environment and load agent
        logger.debug("Initializing environment and loading agent")
        env = MaintenanceEnv(equipment_df, history_df, current_issues)
        agent = MaintenanceAgent(state_size=8, action_size=2)
        agent.load('models/saved/maintenance_dqn_best.pth')
        
        schedule = []
        current_date = datetime.now()
        logger.debug(f"Processing equipment states at {current_date}")
        
        # Iterate through equipment using equipment_id column
        for _, equipment in equipment_df.iterrows():
            try:
                eq_id = equipment['equipment_id']
                logger.debug(f"Processing equipment {eq_id}")
                
                # Get equipment state
                env.current_equipment = equipment
                env.current_date = current_date
                state = env._get_state()
                
                # Get maintenance decision and probability
                actions, probs = agent.predict_maintenance(state.reshape(1, -1))
                maintenance_needed = actions[0] == 1
                confidence = probs[0][1]
                breakdown_risk = float(state[5])
                
                logger.debug(f"Equipment {eq_id} - maintenance needed: {maintenance_needed}, confidence: {confidence:.2f}, risk: {breakdown_risk:.2f}")
                
                if maintenance_needed:
                    # Get current issues for this equipment
                    equipment_issues = current_issues[current_issues['equipment_id'] == eq_id]
                    highest_priority = int(equipment_issues['priority'].min()) if not equipment_issues.empty else 4
                    
                    # Determine maintenance type based on priority and issue type
                    issue_types = equipment_issues['notification_type'].unique() if not equipment_issues.empty else []
                    logger.debug(f"Equipment {eq_id} - priority: {highest_priority}, issue types: {issue_types}")
                    
                    # Priority 1 issues or hydraulic issues get emergency maintenance
                    if highest_priority == 1 or 'HYDR' in issue_types:
                        maint_type = 'PM03' 
                        days_until_maintenance = 1
                    # Priority 2 issues or mechanical/electrical issues get corrective maintenance
                    elif highest_priority == 2 or any(t in issue_types for t in ['MECH', 'ELEC']):
                        maint_type = 'PM02'
                        days_until_maintenance = max(2, min(3, int(5 * (1 - confidence))))
                    # Lower priority issues get preventive maintenance
                    else:
                        maint_type = 'PM01'
                        days_until_maintenance = max(7, min(14, int(14 * (1 - confidence)))) if highest_priority == 3 else max(14, min(30, int(30 * (1 - confidence))))
                    
                    logger.debug(f"Equipment {eq_id} - maintenance type: {maint_type}, days until maintenance: {days_until_maintenance}")
                    
                    schedule.append({
                        'equipment_id': eq_id,
                        'equipment_type': equipment['equipment_type'],
                        'functional_location': equipment['functional_location'],
                        'manufacturer': equipment['manufacturer'],
                        'suggested_date': (current_date + pd.Timedelta(days=days_until_maintenance)).strftime('%Y-%m-%d'),
                        'maintenance_type': maint_type,
                        'priority': 'Critical' if highest_priority == 1 else 'High' if highest_priority == 2 else 'Medium' if highest_priority == 3 else 'Low',
                        'confidence': float(confidence),
                        'breakdown_risk': breakdown_risk,
                        'estimated_duration': max(4, float(env._estimate_maintenance_cost() / 1000))
                    })
                    
            except Exception as e:
                logger.error(f"Error processing equipment {eq_id}: {str(e)}")
                continue
        
        if not schedule:
            logger.error("No maintenance schedule could be generated")
            return jsonify({'error': 'No maintenance schedule could be generated'}), 400
            
        # Save the generated schedule
        schedule_df = pd.DataFrame(schedule)
        schedule_path = os.path.join('data', 'maintenance_schedule.xlsx')
        schedule_df.to_excel(schedule_path, index=False)
        logger.debug(f"Schedule saved to {schedule_path}")
        
        return jsonify(schedule)
        
    except Exception as e:
        logger.error(f"Error in upload_issues: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return jsonify({'error': str(e)}), 500

@app.route('/api/download_template', methods=['GET'])
def download_template():
    try:
        template_path = os.path.join('data', 'sample_data', 'current_issues.csv')
        return send_file(
            template_path,
            mimetype='text/csv',
            as_attachment=True,
            download_name='current_issues_template.csv'
        )
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/download_schedule', methods=['GET'])
def download_schedule():
    try:
        schedule_path = os.path.join('data', 'maintenance_schedule.xlsx')
        return send_file(
            schedule_path,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            as_attachment=True,
            download_name='maintenance_schedule.xlsx'
        )
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)