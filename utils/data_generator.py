import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import os

class MaintenanceDataGenerator:
    def __init__(self, num_machines=10):
        self.num_machines = num_machines
        self.equipment_types = ['FLC', 'RTG', 'QC', 'RS', 'TT']  # Different equipment types
        self.manufacturers = ['GE', 'Siemens', 'ABB', 'Schneider', 'Mitsubishi', 'Hyundai']
        self.criticality_weights = {'A': 0.3, 'B': 0.4, 'C': 0.3}  # Distribution of criticality

    def generate_equipment_master(self):
        """Generate equipment master data similar to SAP PM module"""
        equipment_categories = {
            'PP-PRD': ['Production Line', 'Assembly Station', 'Packaging Unit'],
            'PP-FLC': ['Flow Control', 'Valve System', 'Pump Station'],
            'PP-RTG': ['Routing Equipment', 'Conveyor System', 'Transport Unit'],
            'PP-QM': ['Quality Check Station', 'Testing Unit', 'Inspection System']
        }
        
        manufacturers = ['Siemens', 'ABB', 'Bosch', 'Schneider', 'Rockwell', 'Fanuc']
        maintenance_cycles = [30, 60, 90, 180, 365]  # Days
        
        data = []
        for i in range(self.num_machines):
            category = np.random.choice(list(equipment_categories.keys()))
            equip_type = np.random.choice(equipment_categories[category])
            install_date = self.start_date + timedelta(days=np.random.randint(0, 365*self.history_years))
            
            data.append({
                'equipment_id': f'EQ-{category}-{i:04d}',
                'functional_location': f'PLANT-{category}-{i//20:02d}',
                'equipment_type': equip_type,
                'equipment_category': category,
                'manufacturer': np.random.choice(manufacturers),
                'model_number': f'MDL-{np.random.randint(1000, 9999)}',
                'serial_number': f'SN-{np.random.randint(10000, 99999)}',
                'installation_date': install_date,
                'warranty_expiry': install_date + timedelta(days=365*2),
                'maintenance_cycle': np.random.choice(maintenance_cycles),
                'criticality': np.random.choice(['A', 'B', 'C']),  # A=Critical, B=Important, C=Normal
                'replacement_cost': np.random.uniform(5000, 100000),
                'maintenance_cost_budget': np.random.uniform(1000, 10000),
                'last_major_overhaul': None,
                'technical_status': 'ACTIVE'
            })
        return pd.DataFrame(data)
    
    def generate_equipment_data(self, equipment_ids=None):
        if equipment_ids is None:
            equipment_data = []
            for eq_type in self.equipment_types:
                # Generate some equipment for each type
                num_of_type = max(2, int(self.num_machines / len(self.equipment_types)))
                for i in range(num_of_type):
                    eq_id = f'EQ-PP-{eq_type}-{i:04d}'
                    equipment_data.append(self._create_equipment_record(eq_id, eq_type))
        else:
            equipment_data = [self._create_equipment_record(eq_id, eq_id.split('-')[2]) 
                            for eq_id in equipment_ids]
        
        return pd.DataFrame(equipment_data)

    def _create_equipment_record(self, eq_id, eq_type):
        current_date = datetime.now()
        installation_date = current_date - timedelta(days=np.random.randint(365, 1825))  # 1-5 years old
        warranty_period = np.random.randint(730, 1825)  # 2-5 years warranty
        
        # Maintenance cycle and costs based on equipment type
        cycle_mapping = {
            'FLC': (30, 45),  # Floor conveyor: longer cycles
            'RTG': (15, 30),  # Rubber Tired Gantry: medium cycles
            'QC': (20, 35),   # Quay Crane: medium-long cycles
            'RS': (25, 40),   # Reach Stacker: medium-long cycles
            'TT': (15, 25)    # Terminal Tractor: shorter cycles
        }
        cost_mapping = {
            'FLC': (5000, 8000),
            'RTG': (8000, 12000),
            'QC': (10000, 15000),
            'RS': (6000, 9000),
            'TT': (4000, 7000)
        }
        
        maintenance_cycle = np.random.randint(*cycle_mapping.get(eq_type, (15, 45)))
        replacement_cost = np.random.uniform(*cost_mapping.get(eq_type, (5000, 10000)))
        maintenance_budget = replacement_cost * np.random.uniform(0.8, 1.2)  # Budget varies around replacement cost
        
        # Criticality based on equipment type
        criticality_mapping = {
            'QC': {'A': 0.6, 'B': 0.3, 'C': 0.1},  # QC mostly critical
            'RTG': {'A': 0.4, 'B': 0.4, 'C': 0.2}, # RTG balanced but important
            'FLC': {'A': 0.2, 'B': 0.5, 'C': 0.3}, # FLC mostly medium
            'RS': {'A': 0.3, 'B': 0.4, 'C': 0.3},  # RS balanced
            'TT': {'A': 0.2, 'B': 0.3, 'C': 0.5}   # TT mostly low criticality
        }
        criticality_dist = criticality_mapping.get(eq_type, self.criticality_weights)
        criticality = np.random.choice(['A', 'B', 'C'], p=list(criticality_dist.values()))
        
        return {
            'equipment_id': eq_id,
            'functional_location': f'PLANT-PP-{eq_type}-{eq_id[-2:]}',
            'equipment_type': eq_type,
            'equipment_category': f'PP-{eq_type}',
            'manufacturer': np.random.choice(self.manufacturers),
            'model_number': f'MDL-{np.random.randint(1000, 9999)}',
            'serial_number': f'SN-{np.random.randint(10000, 99999)}',
            'installation_date': installation_date,
            'warranty_expiry': installation_date + timedelta(days=warranty_period),
            'maintenance_cycle': maintenance_cycle,
            'criticality': criticality,
            'replacement_cost': replacement_cost,
            'maintenance_cost_budget': maintenance_budget,
            'last_major_overhaul': None,
            'technical_status': 'ACTIVE'
        }

    def generate_maintenance_history(self, equipment_df):
        """Generate maintenance history data with SAP PM work order structure"""
        maintenance_types = {
            'PM01': 'Preventive',
            'PM02': 'Corrective',
            'PM03': 'Emergency',
            'PM04': 'Modification',
            'PM05': 'Inspection'
        }
        
        activities = {
            'PM01': ['Regular Service', 'Lubrication', 'Component Check', 'Calibration'],
            'PM02': ['Repair', 'Component Replacement', 'Adjustment'],
            'PM03': ['Emergency Repair', 'Breakdown Fix'],
            'PM04': ['Upgrade', 'Modification', 'Enhancement'],
            'PM05': ['Visual Inspection', 'Performance Check', 'Safety Inspection']
        }
        
        data = []
        for _, equipment in equipment_df.iterrows():
            current_date = equipment['installation_date']
            while current_date < datetime.now():
                # Scheduled maintenance
                if np.random.random() < 0.8:  # 80% compliance rate
                    maint_type = 'PM01'
                    duration = np.random.uniform(2, 8)
                    cost = np.random.uniform(500, 2000)
                else:
                    # Random breakdown or emergency
                    maint_type = np.random.choice(['PM02', 'PM03'])
                    duration = np.random.uniform(4, 24)
                    cost = np.random.uniform(1000, 5000)
                
                data.append({
                    'work_order': f'WO-{len(data):06d}',
                    'equipment_id': equipment['equipment_id'],
                    'maintenance_type': maint_type,
                    'activity_type': np.random.choice(activities[maint_type]),
                    'status': 'TECO',  # Technically Completed
                    'start_date': current_date,
                    'end_date': current_date + timedelta(hours=duration),
                    'duration_hours': duration,
                    'actual_cost': cost,
                    'notification': f'NOTIF-{len(data):06d}',
                    'responsible_person': f'TECH-{np.random.randint(1000, 9999)}',
                    'findings': 'Regular maintenance completed'
                })
                
                current_date += timedelta(days=equipment['maintenance_cycle'])
                
                # Random breakdowns (10% chance per cycle)
                if np.random.random() < 0.1:
                    breakdown_date = current_date - timedelta(days=np.random.randint(1, equipment['maintenance_cycle']))
                    data.append({
                        'work_order': f'WO-{len(data):06d}',
                        'equipment_id': equipment['equipment_id'],
                        'maintenance_type': 'PM03',
                        'activity_type': 'Emergency Repair',
                        'status': 'TECO',
                        'start_date': breakdown_date,
                        'end_date': breakdown_date + timedelta(hours=np.random.uniform(4, 24)),
                        'duration_hours': np.random.uniform(4, 24),
                        'actual_cost': np.random.uniform(2000, 8000),
                        'notification': f'NOTIF-{len(data):06d}',
                        'responsible_person': f'TECH-{np.random.randint(1000, 9999)}',
                        'findings': 'Unexpected breakdown - emergency repair required'
                    })
        
        return pd.DataFrame(data)
    
    def generate_current_issues(self, equipment_df):
        """Generate current equipment issues"""
        issue_types = {
            'MECH': ['Vibration', 'Noise', 'Misalignment', 'Wear'],
            'ELEC': ['Power Issues', 'Control Failure', 'Sensor Error'],
            'HYDR': ['Leakage', 'Pressure Loss', 'Flow Issues'],
            'PERF': ['Low Efficiency', 'Quality Issues', 'Speed Variation']
        }
        
        data = []
        for _, equipment in equipment_df.iterrows():
            # 20% chance of current issue
            if np.random.random() < 0.2:
                category = np.random.choice(list(issue_types.keys()))
                data.append({
                    'notification_id': f'NOTIF-{len(data):06d}',
                    'equipment_id': equipment['equipment_id'],
                    'notification_type': category,
                    'issue_description': np.random.choice(issue_types[category]),
                    'priority': np.random.choice(['1', '2', '3', '4']),  # 1=Highest
                    'reported_date': datetime.now() - timedelta(days=np.random.randint(1, 30)),
                    'reported_by': f'USER-{np.random.randint(1000, 9999)}',
                    'status': 'OSNO',  # Outstanding Notification
                    'malfunction_start': datetime.now() - timedelta(days=np.random.randint(1, 5)),
                    'planned_start_date': None,
                    'estimated_cost': np.random.uniform(1000, 5000),
                    'impact': np.random.choice(['Production Stop', 'Quality Impact', 'Performance Degradation', 'Safety Risk'])
                })
        
        return pd.DataFrame(data)
    
    def generate_all_data(self, equipment_ids=None):
        """Generate all datasets and save to CSV"""
        equipment_df = self.generate_equipment_data(equipment_ids)
        history_df = self.generate_maintenance_history(equipment_df)
        issues_df = self.generate_current_issues(equipment_df)
        
        # Save to CSV files
        data_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'sample_data')
        os.makedirs(data_dir, exist_ok=True)
        
        equipment_df.to_csv(os.path.join(data_dir, 'equipment_master.csv'), index=False)
        history_df.to_csv(os.path.join(data_dir, 'maintenance_history.csv'), index=False)
        issues_df.to_csv(os.path.join(data_dir, 'current_issues.csv'), index=False)
        
        return equipment_df, history_df, issues_df