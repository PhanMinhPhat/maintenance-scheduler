# Data Dictionary

## Equipment Master Data (equipment_master.csv)

- `equipment_id`: Unique identifier for each piece of equipment (format: EQ-XX-YYY-NNNN)
- `functional_location`: Physical location of the equipment in the plant (format: PLANT-XX-YYY-NN)
- `equipment_type`: Category of equipment functionality (e.g., Testing Unit, Transport Unit)
- `equipment_category`: Department/area code (e.g., PP-QM, PP-RTG)
- `manufacturer`: Equipment manufacturer name
- `model_number`: Manufacturer's model number (format: MDL-NNNN)
- `serial_number`: Manufacturer's serial number (format: SN-NNNNN)
- `installation_date`: Date when equipment was installed
- `warranty_expiry`: Date when equipment warranty expires
- `maintenance_cycle`: Scheduled maintenance interval in days
- `criticality`: Equipment criticality rating (A, B, C, etc.)
  A: Highest criticality (score 1.0) - Critical equipment where failure would have severe impacts
  B: Medium criticality (score 0.6) - Important equipment with moderate operational impact
  C: Lower criticality (score 0.3) - Equipment with lesser operational impact
- `replacement_cost`: Estimated cost to replace the equipment
- `maintenance_cost_budget`: Allocated budget for maintenance
- `last_major_overhaul`: Date of the last major overhaul
- `technical_status`: Current operational status of equipment (e.g., ACTIVE)

## Maintenance History (maintenance_history.csv)

- `work_order`: Unique identifier for maintenance work order (format: WO-NNNNNN)
- `equipment_id`: Reference to the equipment being maintained
- `maintenance_type`: Type of maintenance performed (PM01: Regular, PM02: Major, PM03: Emergency)
- `activity_type`: Specific maintenance activity performed (e.g., Lubrication, Calibration)
- `status`: Work order status (e.g., TECO: Technically Complete)
- `start_date`: Date and time maintenance work started
- `end_date`: Date and time maintenance work completed
- `duration_hours`: Actual duration of maintenance in hours
- `actual_cost`: Actual cost incurred for the maintenance
- `notification`: Reference to associated notification (format: NOTIF-NNNNNN)
- `responsible_person`: ID of technician performing maintenance (format: TECH-NNNN)
- `findings`: Description of maintenance findings or notes

## Current Issues (current_issues.csv)

- `notification_id`: Unique identifier for issue notification (format: NOTIF-NNNNNN)
- `equipment_id`: Reference to affected equipment
- `notification_type`: Type of issue:
  - PERF: Performance
  - ELEC: Electrical
  - HYDR: Hydraulic
  - MECH: Mechanical
- `issue_description`: Description of the problem
- `priority`: Issue priority level (1: Highest to 4: Lowest)
- `reported_date`: Date and time issue was reported
- `reported_by`: ID of person reporting the issue (format: USER-NNNN)
- `status`: Current status of the notification (e.g., OSNO: Outstanding)
- `malfunction_start`: Date and time when malfunction began
- `planned_start_date`: Planned date to start addressing the issue
- `estimated_cost`: Estimated cost to resolve the issue
- `impact`: Impact of the issue on operations:
  - Production Stop
  - Performance Degradation
  - Quality Impact
  - Safety Risk

## Training History (training_history.csv)

Contains historical training data used for model development

## Maintenance Schedule (maintenance_schedule.xlsx)

Contains planned maintenance schedules and resource allocation data
