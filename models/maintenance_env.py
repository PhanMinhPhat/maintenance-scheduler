import gym
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from gym import spaces

class MaintenanceEnv(gym.Env):
    def __init__(self, equipment_df, history_df, current_issues_df):
        super(MaintenanceEnv, self).__init__()
        
        self.equipment_df = equipment_df
        self.history_df = history_df
        self.current_issues_df = current_issues_df
        self.current_date = datetime.now()
        
        # Action space: [schedule_maintenance, postpone]
        self.action_space = spaces.Discrete(2)
        
        # State space: [days_since_maintenance, equipment_age, criticality_score,
        #              maintenance_cycle_completion, cost_ratio, breakdown_risk,
        #              issue_priority, workload_factor]
        self.observation_space = spaces.Box(
            low=np.array([0, 0, 0, 0, 0, 0, 0, 0]),
            high=np.array([365, 3650, 1, 1, 1, 1, 1, 1]),
            dtype=np.float32
        )
        
        self.reset()
        
    def reset(self):
        """Reset environment to initial state"""
        self.current_date = datetime.now()
        # Select random equipment with active issues
        if len(self.current_issues_df) > 0:
            issue = self.current_issues_df.sample(1).iloc[0]
            self.current_equipment = self.equipment_df[
                self.equipment_df['equipment_id'] == issue['equipment_id']
            ].iloc[0]
        else:
            self.current_equipment = self.equipment_df.sample(1).iloc[0]
            
        return self._get_state()
        
    def step(self, action):
        """
        Take action in environment
        action: 0 = postpone, 1 = schedule maintenance
        """
        reward = 0
        done = False
        
        if action == 1:  # Schedule maintenance
            # Calculate reward based on current state
            state = self._get_state()
            breakdown_risk = state[5]
            issue_priority = state[6]
            
            if breakdown_risk > 0.7 or issue_priority > 0.7:
                reward = 100  # Good decision to maintain
                if issue_priority > 0.9:
                    reward += 50  # Extra reward for addressing critical issues
            else:
                reward = -50  # Unnecessary maintenance
                
            # Consider maintenance costs
            maintenance_cost = self._estimate_maintenance_cost()
            budget = self.current_equipment['maintenance_cost_budget']
            cost_penalty = -20 * (maintenance_cost / budget)
            reward += cost_penalty
            
        else:  # Postpone maintenance
            state = self._get_state()
            breakdown_risk = state[5]
            issue_priority = state[6]
            
            if breakdown_risk > 0.9 or issue_priority > 0.8:
                reward = -200  # High risk of failure
            else:
                reward = 10  # Good decision to wait
                
        # Move to next day
        self.current_date += timedelta(days=1)
        next_state = self._get_state()
        
        # Episode ends after 30 days or if equipment fails
        done = (self.current_date - datetime.now()).days >= 30 or breakdown_risk > 0.95
        
        return next_state, reward, done, {}
        
    def _get_state(self):
        """Get current state representation"""
        days_since_maintenance = self._get_days_since_last_maintenance()
        equipment_age = (self.current_date - pd.to_datetime(self.current_equipment['installation_date'])).days
        criticality_score = self._get_criticality_score()
        maintenance_cycle_completion = days_since_maintenance / self.current_equipment['maintenance_cycle']
        cost_ratio = self._get_cost_ratio()
        breakdown_risk = self._calculate_breakdown_risk()
        issue_priority = self._get_issue_priority()
        workload_factor = self._get_workload_factor()
        
        return np.array([
            days_since_maintenance / 365,  # Normalize to [0,1]
            equipment_age / 3650,  # Normalize to [0,1] (10 years max)
            criticality_score,
            maintenance_cycle_completion,
            cost_ratio,
            breakdown_risk,
            issue_priority,
            workload_factor
        ], dtype=np.float32)
        
    def _get_days_since_last_maintenance(self):
        """Calculate days since last maintenance"""
        relevant_history = self.history_df[
            self.history_df['equipment_id'] == self.current_equipment.name
        ]
        if len(relevant_history) == 0:
            return 365  # Max value if no maintenance history
            
        last_maintenance = pd.to_datetime(
            relevant_history['end_date']
        ).max()
        
        return (self.current_date - last_maintenance).days
        
    def _get_criticality_score(self):
        """Convert equipment criticality to score"""
        criticality_map = {'A': 1.0, 'B': 0.6, 'C': 0.3}
        return criticality_map[self.current_equipment['criticality']]
        
    def _get_cost_ratio(self):
        """Calculate maintenance cost ratio"""
        relevant_history = self.history_df[
            self.history_df['equipment_id'] == self.current_equipment.name
        ]
        if len(relevant_history) == 0:
            return 0.5
            
        avg_cost = relevant_history['actual_cost'].mean()
        return min(avg_cost / self.current_equipment['maintenance_cost_budget'], 1.0)
        
    def _calculate_breakdown_risk(self):
        """Calculate risk of breakdown"""
        days_since_maintenance = self._get_days_since_last_maintenance()
        maintenance_cycle = self.current_equipment['maintenance_cycle']
        base_risk = min(days_since_maintenance / maintenance_cycle, 1.0)
        
        # Increase risk based on age
        age_years = (self.current_date - pd.to_datetime(self.current_equipment['installation_date'])).days / 365
        age_factor = min(age_years / 10, 1.0)  # Assumes 10 year expected lifetime
        
        # Increase risk if there are current issues
        has_issues = len(self.current_issues_df[
            self.current_issues_df['equipment_id'] == self.current_equipment.name
        ]) > 0
        
        issue_factor = 0.2 if has_issues else 0
        
        return min(base_risk + (0.3 * age_factor) + issue_factor, 1.0)
        
    def _get_issue_priority(self):
        """Get priority score of current issues"""
        current_issues = self.current_issues_df[
            self.current_issues_df['equipment_id'] == self.current_equipment.name
        ]
        
        if len(current_issues) == 0:
            return 0.0
            
        # Convert priority to score (1=Highest -> 1.0, 4=Lowest -> 0.25)
        priority_scores = current_issues['priority'].astype(int).map(lambda x: 1.25 - (x * 0.25))
        return float(priority_scores.max())
        
    def _get_workload_factor(self):
        """Calculate maintenance workload factor for current date"""
        window_start = self.current_date - timedelta(days=7)
        window_end = self.current_date + timedelta(days=7)
        
        scheduled_maintenance = self.history_df[
            (pd.to_datetime(self.history_df['start_date']) >= window_start) &
            (pd.to_datetime(self.history_df['start_date']) <= window_end)
        ]
        
        daily_count = len(scheduled_maintenance) / 15  # 15 days window
        return min(daily_count / 5, 1.0)  # Normalize assuming max 5 maintenances per day
        
    def _estimate_maintenance_cost(self):
        """Estimate cost of maintenance based on history"""
        relevant_history = self.history_df[
            self.history_df['equipment_id'] == self.current_equipment.name
        ]
        if len(relevant_history) == 0:
            return self.current_equipment['maintenance_cost_budget'] * 0.5
            
        return relevant_history['actual_cost'].mean()