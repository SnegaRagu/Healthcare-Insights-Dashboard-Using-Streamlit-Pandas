USE project_healthcare;

/*
Q1. Trends in Admission Over Time
*/
	
    SELECT
		date_format(admit_date, '%Y-%m') AS month,
		count(*) AS monthly_patient_admissions 
	FROM 
		healthcare
	GROUP BY 
		month
	ORDER BY 
		month;
    
/*
Q2. Diagnosis Frequency Analysis: Identify the top 5 most common diagnoses
*/
	SELECT 
		diagnosis, 
		count(diagnosis) as diagnosis_count 
	FROM 
		healthcare
	GROUP BY 
		diagnosis
	ORDER BY 
		count(diagnosis) DESC
		LIMIT 5;
    
/*
Q3. Bed Occupancy Analysis: Analyze the distribution of bed occupancy types
*/

DROP TABLE IF EXISTS bed_occupancy_analysis;
CREATE TABLE bed_occupancy_analysis AS
	WITH monthly_admissions AS(
		SELECT 
			bed_occupancy,
			count(*) as total_admissions,
			date_format(admit_date,'%Y-%m') as month
		FROM 
			healthcare AS a
		GROUP BY 
			month, bed_occupancy
	),
	monthly_discharges AS(
		SELECT
			bed_occupancy,
			count(*) AS total_discharges,
			date_format(discharge_date,'%Y-%m') as month
		FROM
			healthcare as d
		GROUP BY
			month, bed_occupancy
	)
		SELECT
			COALESCE(a.month, d.month) AS month,
			COALESCE(a.bed_occupancy, d.bed_occupancy) AS bed_occupancy,
			COALESCE(a.total_admissions, 0) as total_monthly_admissions,
			COALESCE(d.total_discharges, 0) as total_monthly_discharges
		FROM
			monthly_admissions a
		LEFT JOIN
			monthly_discharges d
		ON
			a.month = d.month AND a.bed_occupancy = d.bed_occupancy
	UNION
		SELECT
			COALESCE(a.month, d.month),
			COALESCE(a.bed_occupancy, d.bed_occupancy) AS bed_occupancy,
			COALESCE(a.total_admissions, 0) AS total_monthly_admissions,
			COALESCE(d.total_discharges, 0) AS total_monthly_discharges
		FROM
			monthly_discharges d
		LEFT JOIN
			monthly_admissions a
		ON
			a.month = d.month AND a.bed_occupancy =  d.bed_occupancy
	ORDER BY month;
 
 SELECT * FROM bed_occupancy_analysis;
    
/*
Q4. Length of Stay Distribution: Analyze the average and maximum length of stay for patients
*/

	SELECT
		diagnosis,
		ROUND(avg(datediff(discharge_date, admit_date)), 2) as avg_stay,
        max(datediff(discharge_date, admit_date)) as max_stay
    FROM 
		healthcare
	GROUP BY
		diagnosis;

		SELECT
			diagnosis,
			ROUND(avg(datediff(discharge_date, admit_date)), 2) as avg_stay
		FROM 
			healthcare
		GROUP BY
			diagnosis;
/*
Q5. Seasonal Admission Patterns: Identify the seasonality in admissions based on the month.
*/

	SELECT
		YEAR(admit_date) AS Years,
		CASE
			WHEN MONTH(admit_date) IN (12, 1, 2) THEN 'Winter'
            WHEN MONTH(admit_date) IN (3, 4, 5) THEN 'Summer'
            WHEN MONTH(admit_date) IN (6, 7, 8) THEN 'Monsoon'
            WHEN MONTH(admit_date) In (9, 10, 11) THEN 'Autumn'
		END AS season,
        COUNT(*) AS Seasonal_Admissions
	FROM
		healthcare
	GROUP BY 
		Years, season;
        
/*
Q6. TEST CONDUCTED AS PER DIAGNOSIS
*/

SELECT DISTINCT test FROM healthcare;

	SELECT
		diagnosis,
        SUM(CASE WHEN test='Blood Test' THEN 1 ELSE 0 END) AS BLOOD_TEST,
		SUM(CASE WHEN test='MRI' THEN 1 ELSE 0 END) AS MRI,
		SUM(CASE WHEN test='CT SCAN' THEN 1 ELSE 0 END) AS CT_SCAN,
		SUM(CASE WHEN test='X-RAY' THEN 1 ELSE 0 END) AS X_RAY,
		SUM(CASE WHEN test='Ultrasound' THEN 1 ELSE 0 END) AS ULTRASOUND,
		COUNT(*) AS Total_tests
	FROM
		healthcare
	GROUP BY
		diagnosis
	ORDER BY
		Total_tests DESC;

/*
Q7. BILLING ANALYSIS AS PER DIAGNOSIS
*/

	SELECT
		YEAR(admit_date) as Years,
		diagnosis,
        SUM(billing_amount) AS Total_billing,
		COUNT(patient_id) AS Number_of_visits,
        ROUND(AVG(billing_amount) ,2) AS Average_billing_per_visit
	FROM 
		healthcare
	GROUP BY 
		Years, diagnosis
	ORDER BY 
		Average_billing_per_visit DESC;

/*
Q8. PATIENTS INSURANCE COVERAGE STATUS AS PER DIAGNOSIS
*/

	SELECT
		diagnosis,
        SUM(billing_amount) AS Total_billing_amount,
        SUM(health_insurance_amount) AS Total_insurance_covered,
        COUNT(*) AS Number_of_patients,
        ROUND(100.0 * (SUM(health_insurance_amount)) / (SUM(billing_amount)), 2) AS Coverage_percentage
	FROM
		healthcare
	GROUP BY
		diagnosis
	ORDER BY
		Coverage_percentage DESC;

/*
Q9. MOST RATED DOCTOR
*/

	SELECT 
		DISTINCT doctor,
		GROUP_CONCAT(DISTINCT diagnosis ORDER BY diagnosis SEPARATOR ',') AS diagnosis,
		feedback,
		COUNT(*) AS number_of_ratings
	FROM 
		healthcare
	WHERE 
		feedback = 5
	GROUP BY 
		doctor
	ORDER BY 
		number_of_ratings DESC;

/*
Q10. OVERALL PATIENT TEST COUNT
*/

	SELECT 
	  test,
	  COUNT(*) AS test_count
	FROM 
		healthcare
	GROUP BY 
		test
	ORDER BY 
		test_count DESC;


/*
Q11. Follow-Up Compliance Rate
*/

	SELECT
		diagnosis,
		CASE
			WHEN followup_date IS NOT NULL THEN 'Followup present'
            ELSE 'No Followup'
		END AS followup_status,
        count(*) AS Patient_count
	FROM
		healthcare
	GROUP BY
		diagnosis,
		followup_status;

/*
Q12. Doctor Workload Distribution
*/

	SELECT
		YEAR(admit_date) as Years,
		doctor,
        COUNT(DISTINCT patient_id) AS Patients_attended,
        ROUND(AVG(feedback), 2) AS Average_feedback
	FROM
		healthcare
	GROUP BY
		Years,
		doctor
	ORDER BY
		Years,
		Patients_attended DESC;
        
/*
Q13.Follow-Up Time Line
*/

	SELECT
		diagnosis,
        ROUND(AVG(DATEDIFF(followup_date, discharge_date)),2) AS avg_followup_delay,
        COUNT(*) AS Total_Followups,
        SUM(CASE WHEN DATEDIFF(followup_date, discharge_date) > 30 THEN 1 ELSE 0 END) AS Late_Followups,
        ROUND(SUM(CASE WHEN DATEDIFF(followup_date, discharge_date) < 30 THEN 1 ELSE 0 END) / COUNT(*) * 100, 2
			 ) AS Early_Followup_Percantage,
		ROUND(SUM(CASE WHEN DATEDIFF(followup_date, discharge_date) > 30 THEN 1 ELSE 0 END) / COUNT(*) * 100, 2
			 ) AS Late_Followup_Percantage
	FROM
		healthcare
	WHERE
		followup_date IS NOT NULL
        AND 
        discharge_date IS NOT NULL
	GROUP BY
		diagnosis
	ORDER BY
		Late_Followup_Percantage DESC;
        
/*
Q14. Lab Supply Distribution According To Tests Conducted Over Years
*/
SET SESSION sql_mode=(SELECT REPLACE(@@sql_mode,'ONLY_FULL_GROUP_BY',''));
	SELECT
		YEAR(admit_date) AS Years,
        SUM(CASE WHEN test='Blood Test' THEN 1 ELSE 0 END) AS BLOOD_TEST,
		SUM(CASE WHEN test='MRI' THEN 1 ELSE 0 END) AS MRI,
		SUM(CASE WHEN test='CT SCAN' THEN 1 ELSE 0 END) AS CT_SCAN,
		SUM(CASE WHEN test='X-RAY' THEN 1 ELSE 0 END) AS X_RAY,
		SUM(CASE WHEN test='Ultrasound' THEN 1 ELSE 0 END) AS ULTRASOUND,
        COUNT(*) AS Number_of_tests
	FROM
		healthcare
	GROUP BY
		Years;
        
/*
Q15. Doctor-Wise Patient Recovery Time Analysis
*/

	SELECT 
		doctor,
        COUNT(*) AS Total_patients,
        MIN(DATEDIFF(discharge_date, admit_date)) AS min_recovery_days,
        ROUND(AVG(DATEDIFF(discharge_date, admit_date)), 2) AS avg_recovery_days,
        MAX(DATEDIFF(discharge_date, admit_date)) AS max_recovery_days
	FROM
		healthcare
	GROUP BY
		doctor
	ORDER BY
		avg_recovery_days DESC;
        
/*
Q16. Net Revenue Per Patient Over Years
*/

	SELECT
		YEAR(admit_date) as Years,
        COUNT(*) AS Total_patients,
        SUM(billing_amount - health_insurance_amount) AS Net_Revenue,
        AVG(billing_amount - health_insurance_amount) AS Avg_Revenue_Per_Patient
	FROM
		healthcare
	GROUP BY
		Years
	ORDER BY
		Years;