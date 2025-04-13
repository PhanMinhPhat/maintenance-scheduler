import torch
import pandas as pd
import numpy as np
from datetime import datetime
import os
import json

from models.maintenance_env import MaintenanceEnv
from models.dqn_agent import MaintenanceAgent
from utils.data_generator import MaintenanceDataGenerator

def train_model(num_episodes=1000, batch_size=64):
    # Generate or load training data
    data_gen = MaintenanceDataGenerator(num_machines=100)
    equipment_df, history_df, issues_df = data_gen.generate_all_data()
    
    # Initialize environment and agent
    env = MaintenanceEnv(equipment_df, history_df, issues_df)
    state_size = env.observation_space.shape[0]
    action_size = env.action_space.n
    
    agent = MaintenanceAgent(
        state_size=state_size,
        action_size=action_size,
        batch_size=batch_size
    )
    
    # Training metrics
    best_reward = float('-inf')
    training_history = []
    
    # Training loop
    for episode in range(num_episodes):
        state = env.reset()
        total_reward = 0
        done = False
        
        while not done:
            # Select and perform action
            action = agent.act(state)
            next_state, reward, done, _ = env.step(action)
            
            # Store experience in memory
            agent.remember(state, action, reward, next_state, done)
            
            # Train the network
            loss = agent.train()
            
            state = next_state
            total_reward += reward
        
        # Save training metrics
        training_history.append({
            'episode': episode + 1,
            'total_reward': total_reward,
            'epsilon': agent.epsilon,
            'loss': loss if loss else 0
        })
        
        # Save best model
        if total_reward > best_reward:
            best_reward = total_reward
            agent.save(f'models/saved/maintenance_dqn_best.pth')
        
        # Log progress
        if (episode + 1) % 10 == 0:
            print(f"Episode {episode + 1}/{num_episodes}, "
                  f"Reward: {total_reward:.2f}, "
                  f"Epsilon: {agent.epsilon:.2f}, "
                  f"Loss: {loss if loss else 0:.4f}")
    
    # Save training history
    history_df = pd.DataFrame(training_history)
    history_df.to_csv('data/training_history.csv', index=False)
    
    # Save final model
    agent.save('models/saved/maintenance_dqn_final.pth')
    
    return agent, history_df

def generate_maintenance_schedule(agent, env, num_days=30):
    """Generate maintenance schedule for all equipment"""
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
            equipment_issues = env.current_issues_df[env.current_issues_df['equipment_id'] == equipment.name]
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
                'suggested_date': (current_date + pd.Timedelta(days=days_until_maintenance)).strftime('%Y-%m-%d'),
                'maintenance_type': maint_type,
                'priority': priority,
                'confidence': float(confidence),
                'breakdown_risk': float(state[5]),
                'estimated_duration': float(env._estimate_maintenance_cost() / 100)  # Rough estimate in hours
            })
    
    return pd.DataFrame(schedule)

if __name__ == "__main__":
    # Train model
    agent, history = train_model()
    
    # Generate sample schedule
    data_gen = MaintenanceDataGenerator()
    equipment_df, history_df, issues_df = data_gen.generate_all_data()
    env = MaintenanceEnv(equipment_df, history_df, issues_df)
    
    schedule_df = generate_maintenance_schedule(agent, env)
    schedule_df.to_excel('data/maintenance_schedule.xlsx', index=False)
    print("\nMaintenance schedule generated and saved to 'data/maintenance_schedule.xlsx'")