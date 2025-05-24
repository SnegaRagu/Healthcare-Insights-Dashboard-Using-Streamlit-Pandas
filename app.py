# Importing Libraries

import streamlit as st
import pandas as pd
import pymysql
from sqlalchemy import create_engine, text
import plotly.express as px
from plotly.subplots import make_subplots
import plotly.graph_objects as go

# Database Connection Setup

DB_USER = 'root'
DB_PASSWORD = 'root'
DB_HOST = 'localhost'
DB_PORT = '3306'
DB_NAME = 'project_healthcare'

# MYSQL Connection

engine = create_engine(f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}")

st.title("Healthcare Insights Dashboard")

# |------------------------------------- QUERY - 1 -----------------------------------------------|
# Trends in Admission Over Time: Analyze monthly patient admissions to identify trends over time.

with st.expander("Trends in Admission Over Time: Analyze monthly patient admissions to identify trends over time"):
	st.subheader("Trends in Admission Over Time")
	st.write("Fetching frequency of admission from helathcare dataset via MYSQL query")
	query1 = """    
		SELECT
			date_format(admit_date, '%%Y-%%m') AS month,
			count(*) AS monthly_patient_admissions 
		FROM 
			healthcare
		GROUP BY 
			month
		ORDER BY 
			month;
	"""

	# Query to Dataframe
	df1 = pd.read_sql(query1, con=engine)

	# Result Display
	st.dataframe(df1)

	# Plot
	fig1 = px.bar(df1,
				x = 'month',
				y = 'monthly_patient_admissions',
				title = 'Admission Trends',
				text_auto=True,
				color='monthly_patient_admissions')

	st.plotly_chart(fig1, use_container_width=True)
	st.subheader("Admission Trend Insights")
	st.markdown("""
		* March 2024 and December 2022 has lower admission rate
		* March 2023 has higher admissions
		 """)

# |------------------------------------- QUERY - 2 -----------------------------------------------|
# Diagnosis Frequency Analysis: Identify the top 5 most common diagnoses

with st.expander("Diagnosis Frequency Analysis: Identify the top 5 most common diagnoses"):
	st.subheader("Diagnosis Frequency Analysis")
	st.write("Fetching frequency of diagnosis from helathcare dataset via MYSQL query")
	query2 = """
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
	"""

	df2 = pd.read_sql(query2, con=engine)
	st.dataframe(df2)

	fig2 = px.pie(df2,
			   values='diagnosis_count',
			   names='diagnosis',
			   title='Top Diagnosis')

	st.plotly_chart(fig2, use_container_width=True)
	st.subheader("Diagnosis Insights")
	st.markdown("""
		* Viral Infection is the most diagnosed disease
		* Followed by Flu, Malaria, typhoid, Pneumonia
		 """)

# |------------------------------------- QUERY - 3 -----------------------------------------------|
# Bed Occupancy Analysis: Analyze the distribution of bed occupancy types

with st.expander("Bed Occupancy Analysis: Analyze the distribution of bed occupancy types"):
	st.subheader("Bed Occupancy Analysis")
	st.write("Fetching bed occupancy data from Healthcare database using MYSQL Query")
	with engine.begin() as conn:
		# Drop
		conn.execute(text("DROP TABLE IF EXISTS bed_occupancy_analysis;"))

		# Create
		conn.execute(text("""
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
					a.month = d.month AND a.bed_occupancy = d.bed_occupancy
			ORDER BY month;
		"""))

	# Select
	query3 = " SELECT * FROM bed_occupancy_analysis;"

	df3 = pd.read_sql(query3, con=engine)
	st.dataframe(df3)

	# Separating Admissions and Discharges
	admissions_pivot = df3.pivot_table(index='month',columns='bed_occupancy',values='total_monthly_admissions',fill_value=0)
	discharges_pivot = df3.pivot_table(index='month',columns='bed_occupancy',values='total_monthly_discharges',fill_value=0)

	# Setting subplots
	fig3 = make_subplots(rows=2, cols=1, shared_xaxes=True, subplot_titles=("Admission_Bed_Occupancy", "Discharge_Bed_Occupancy"))
	
	# Add Traces
	for col in admissions_pivot.columns:
		fig3.add_trace(go.Bar(name = str(col), 
								x = admissions_pivot.index, 
								y = admissions_pivot[col]
							), row=1, col=1)
	for col in discharges_pivot.columns:
		fig3.add_trace(go.Bar(name = str(col), 
								x = discharges_pivot.index, 
								y = discharges_pivot[col]
							), row=2, col=1)

	# Update X-axis properties
	fig3.update_xaxes(title_text="Month", row=1, col=1)
	fig3.update_xaxes(title_text="Month", row=2, col=1)

	# Update Y-axis properties
	fig3.update_yaxes(title_text="Admissions", row=1, col=1)
	fig3.update_yaxes(title_text="Discharges", row=2, col=1)

	fig3.update_layout(barmode='stack', title_text='Bed occupancy', height=750)

	st.plotly_chart(fig3)
	st.subheader("Bed Occupancy Insights")
	st.markdown("""
		* March 2023 has higher admission and discharge rates
		* Mostly private beds are occupied across the years
		 """)

# |------------------------------------- QUERY - 4 -----------------------------------------------|
# Length of Stay Distribution: Analyze the average and maximum length of stay for patients

with st.expander("Length of Stay Distribution: Analyze the average and maximum length of stay for patients"):
	st.subheader("Length of Stay Distribution")
	st.write("Fetching patients stay distribution in hospital from Healthcare database using MYSQL Query")
	query4 = """
		SELECT
			diagnosis,
			ROUND(avg(datediff(discharge_date, admit_date)), 2) as avg_stay,
			max(datediff(discharge_date, admit_date)) as max_stay
		FROM 
			healthcare
		GROUP BY
			diagnosis;
	"""

	df4 = pd.read_sql(query4, con=engine)

	st.dataframe(df4)

	fig4 = px.bar(df4, 
			   		x='diagnosis', 
					y='avg_stay', 
					title='Average Stay per Diagnosis', 
					text_auto=True,
					color='avg_stay')

	fig4.update_layout(title_text='Average Length of Stay Distribution per Diagnosis', showlegend=False)
	fig4.update_xaxes(title_text='Diagnosis')
	fig4.update_yaxes(title_text='Days')

	st.plotly_chart(fig4, height = 300)

	fig41 = px.bar(df4, 
			   		x='diagnosis', 
					y='max_stay', 
					title='Maximum Stay per Diagnosis', 
					text_auto=True)

	fig41.update_layout(title_text='Maximum Length of Stay Distribution per Diagnosis', showlegend=False)
	fig41.update_xaxes(title_text='Diagnosis')
	fig41.update_yaxes(title_text='Days')

	st.plotly_chart(fig41, height=300)
	st.subheader("Stay distribution Insights")
	st.markdown("""
		* Across all years, Malaria patients have longer stay
		* Pnuemonia patients have lower stay distribution on an average
		* For all diagnosis, patients stayed maximum of 45 days.
		 """)

# |------------------------------------- QUERY - 5 -----------------------------------------------|
# Seasonal Admission Patterns: Identify the seasonality in admissions based on the month

with st.expander("Seasonal Admission Patterns: Identify the seasonality in admissions based on the month"):
	st.subheader("Seasonal Admission Patterns")
	st.write("Fetching patients seasonal admissions details from Healthcare database using MYSQL Query")
	query5 = """
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
	"""

	df5 = pd.read_sql(query5, con=engine)
	st.dataframe(df5)

	fig5 = px.bar(df5,
				x = 'Years',
				y = 'Seasonal_Admissions',
				color = 'season',
				title = 'Seasonwise Admissions',
				barmode = 'stack',
				text_auto = True)
	
	st.plotly_chart(fig5)
	st.subheader("Seasonal Admission Insights")
	st.markdown("""
		* Across all years, winter has most patients admitted to hospitals
		* Autumn has least patients admitted in 2023.
		 """)

# |------------------------------------- QUERY - 6 -----------------------------------------------|
# Tests Conducted As Per Diagnosis

with st.expander("Tests Conducted As Per Diagnosis"):
	st.subheader("Tests Conducted As Per Diagnosis")
	st.write("Fetching the test conducted details according to the diagnosis from Healthcare database using MYSQL Query")
	query6 = """
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
	"""

	df6 = pd.read_sql(query6, con=engine)
	st.dataframe(df6)

	# Remove 'Total_tests' before melt to avoid conflict
	df6_f = df6.drop(columns=['Total_tests'])

	# Dataframe melt to long format
	df_m = df6_f.melt(id_vars='diagnosis', var_name='tests', value_name='total_tests')

	# Categorising unique values
	diagnosis_list = df6_f['diagnosis'].unique().tolist()
	test_list =  ['BLOOD_TEST', 'MRI', 'CT_SCAN', 'X_RAY', 'ULTRASOUND']

	# Mapping categoric values to numeric indices
	df_m['diagnosis_m'] = df_m['diagnosis'].apply(lambda x : diagnosis_list.index(x))
	df_m['tests_m'] = df_m['tests'].apply(lambda x : test_list.index(x))

	# 3D Scatter Plot
	fig6 = go.Figure(data=[go.Scatter3d(x = df_m['diagnosis_m'],
									 	y = df_m['tests_m'],
										z = df_m['total_tests'],
										mode = 'markers',
										marker = dict(size=8, color=df_m['total_tests'], colorscale='Viridis'),
										text = df_m[['diagnosis','tests','total_tests']].astype(str).agg(' | '.join, axis=1)
										)])
	
	fig6.update_layout(scene=dict(
								xaxis=dict(title='diagnosis-x'),
							   	yaxis=dict(title='tests-y'),
								zaxis=dict(title='total_tests-z')),
						title='3D Scatter Plot for Tests Per Diagnosis')
	st.plotly_chart(fig6)
	st.subheader("Test vs Diagnosis Insights")
	st.markdown("""
		* Overall, Blood test is conducted 625 times for viral infection
		* Ultrasound is least taken test for fracture of about 36 times.
		 """)
# |------------------------------------- QUERY - 7 -----------------------------------------------|
# Billing Analysis As Per Diagnosis 

with st.expander("Billing Analysis As Per Diagnosis"):
	st.subheader("Billing Analysis As Per Diagnosis")
	st.write("Fetching billing data from Healthcare database using MYSQL Query")
	query7 = """
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
	"""

	df7 = pd.read_sql(query7, con=engine)
	st.dataframe(df7)

	df7_2022 = df7[df7['Years'] == 2022]
	fig7_2022 = px.bar(df7_2022,
					x='Years',
					y='Total_billing',
					title='2022 Net billing analysis over diagnosis',
					text_auto = True,
					color='diagnosis',
					barmode='group')
	
	fig7_2022.update_layout(yaxis=dict(range=[0, df7_2022['Total_billing'].max() * 1.1]))

	st.plotly_chart(fig7_2022)

	df7_2023 = df7[df7['Years'] == 2023]
	fig7_2023 = px.bar(df7_2023,
					x='Years',
					y='Total_billing',
					title='2023 Net billing analysis over diagnosis',
					text_auto = True,
					color='diagnosis',
					barmode='group')
	
	fig7_2023.update_layout(yaxis=dict(range=[0, df7['Total_billing'].max() * 1.1]))

	st.plotly_chart(fig7_2023)


	df7_2024 = df7[df7['Years'] == 2024]
	fig7_2024 = px.bar(df7_2024,
					x='Years',
					y='Total_billing',
					title='2024 Net billing analysis over years',
					text_auto = True,
					color='diagnosis',
					barmode='group')
	
	fig7_2024.update_layout(yaxis=dict(range=[0, df7_2024['Total_billing'].max() * 1.1]))

	st.plotly_chart(fig7_2024)
	st.subheader("Billing Analysis Insights")
	st.markdown("""
		1) 2022 
			 * Flu is billed highly, whereas Fracture billing is low
		2) 2023
			 * Viral infection billing is high whereas Flu billing is lower
		3) 2024
			 * Flu billing is higher whereas Fracture billing is lower.
		 """)

# |------------------------------------- QUERY - 8 -----------------------------------------------|
# Patients Insurance Coverage Status As Per Diagnosis

with st.expander("Patients Insurance Coverage Status As Per Diagnosis"):
	st.subheader("Patients Insurance Coverage Analysis")
	st.write("Fetching patients insurance coverage status as per diagnosis from Healthcare database using MYSQL Query")
	query8 = """
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
	"""

	df8 = pd.read_sql(query8, con=engine)
	st.dataframe(df8)

	fig8 = go.Figure()
	fig8.add_trace(go.Bar(x=df8['diagnosis'],
								y=df8['Total_billing_amount'],
								name='Billed Amount',
								opacity=0.75))
	fig8.add_trace(go.Bar(x=df8['diagnosis'],
								y=df8['Total_insurance_covered'],
								name='Insured Amount',
								opacity=0.75))
	fig8.update_layout(title="Insurance Analysis",
						xaxis=dict(title='Diagnosis'),
						yaxis=dict(title='Amount'),
						barmode='group')

	st.plotly_chart(fig8)
	st.subheader("Insurance Analysis Insights")
	st.markdown("""
		* Viral infection has the most insurance coverage
		* Almost 90% of billing is covered with insurance of patients
		 """)

# |------------------------------------- QUERY - 9 -----------------------------------------------|
# Most Rated Doctor

with st.expander("Most Rated Doctor"):
	st.subheader("Most Rated Doctor")
	st.write("Fetching doctor's most valued feedback data from Healthcare database using MYSQL Query")
	query9 = """
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
	"""

	df9 = pd.read_sql(query9, con=engine)
	st.dataframe(df9)

	fig9 = px.bar(df9,
			   	  x='doctor',
				  y='number_of_ratings',
				  title='5 Star Rated doctors',
				  text_auto=True,
				  color='doctor')
	
	st.plotly_chart(fig9)
	st.subheader("Doctor Rating Insights")
	st.markdown("""
		* Dr. Jaya Yaadav and Dr.Tejas Saxena are the most 5 rated doctors.
		 """)

# |------------------------------------- QUERY - 10 -----------------------------------------------|
# Overall Patient Test Count

with st.expander("Overall Patient Test Count"):
	st.subheader("Overall Patient Test Count")
	st.write("Fetching overall patient's test details from Healthcare database using MYSQL Query")
	query10 = """
		SELECT 
			test,
			COUNT(*) AS test_count
		FROM 
			healthcare
		GROUP BY 
			test
		ORDER BY 
			test_count DESC;
	"""

	df10 = pd.read_sql(query10, con=engine)
	st.dataframe(df10)

	fig10 = px.bar(df10,
					   x='test',
					   y='test_count',
					   title='Patient Tests Conducted',
					   color='test',
					   text_auto=True)
	st.plotly_chart(fig10)
	st.subheader("Overall Patient Test Insights")
	st.markdown("""
		* Blood test is the most taken tests around 2236.
		* Ultrasound is the least taken tests in the hospital.
		 """)

# |------------------------------------- QUERY - 11 -----------------------------------------------|
# Follow-Up Compliance Rate

with st.expander("Follow-Up Compliance Rate"):
	st.subheader("Follow-Up Compliance Rate")
	st.write("Fetching whether patients have followups or not from Healthcare database using MYSQL Query")
	query11 = 	"""
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
	"""

	df11 = pd.read_sql(query11, con=engine)
	st.dataframe(df11)

	fig11 = px.bar(df11,
				y='diagnosis',
				x='Patient_count',
				title='Patient Follow-up Status by Diagnosis',
				barmode='group',
				color='followup_status',
				text_auto=True)
	fig11.update_layout(legend_title="Legende")
	st.plotly_chart(fig11)
	st.subheader("Followup Compliance Insights")
	st.markdown("""
		* Acute infections like Flu, Viral infection has comparatively low no-followup rate
		* Fracture patients have high-followup rate
		 """)

# |------------------------------------- QUERY - 12 -----------------------------------------------|
# Doctor Workload Distribution

with st.expander("Doctor Workload Distribution"):
	st.subheader("Doctor Workload Distribution")
	st.write("Fetching doctor workload distribution data from Healthcare database using MYSQL Query")
	query12 = """
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
	"""

	df12 = pd.read_sql(query12, con=engine)
	st.dataframe(df12)

	df12_2022 = df12[df12['Years'] == 2023]
	fig12_22 = px.bar(df12_2022,
					y='doctor',
					x='Patients_attended',
					title='2023 - Doctors workload plot',
					text_auto=True,
					color='doctor')	
	
	st.plotly_chart(fig12_22)

	df12_202x = df12[df12['Years'].isin([2022,2024])]
	fig12_2x = px.bar(df12_202x,
					y='doctor',
					x='Patients_attended',
					title='2022 & 2024 - Doctors workload plot',
					text_auto=True,
					color='Years')	
	
	st.plotly_chart(fig12_2x)
	st.subheader("Doctor workload Insights")
	st.markdown("""
		* Across all years, all doctor have almost equal work allocation.
		 """)

# |------------------------------------- QUERY - 13 -----------------------------------------------|
# Follow-Up Time Line

with st.expander("Follow-Up Time Line"):
	st.subheader("Follow-Up Time Line")
	st.write("Fetching Followup checkups data from Healthcare database using MYSQL Query")
	query13 = """
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
	"""

	df13 = pd.read_sql(query13, con=engine)
	st.dataframe(df13)

	fig131 = px.bar(df13,
				 	x='diagnosis',
					y='avg_followup_delay',
					title='Average delays for followups as per diagnosis',
					text_auto=True,
					color='diagnosis')
	st.plotly_chart(fig131)

	fig132 = go.Figure()
	fig132.add_trace(go.Scatter(x=df13['diagnosis'],
							 	y=df13['Early_Followup_Percantage'],
								mode='markers+lines',
								name='Early'))
	
	fig132.add_trace(go.Scatter(x=df13['diagnosis'],
							 	y=df13['Late_Followup_Percantage'],
								mode='markers+lines',
								name='Late'))
	
	fig132.update_layout(title='Early Vs Late Followup Percentage Chart',
					  	xaxis_title='Diagnosis',
						yaxis_title='Percentage')
	st.plotly_chart(fig132)
	st.subheader("Followup time line Insights")
	st.markdown("""
		* Average followup delay is about 10-11 days after discharge
		* 19% of Malaria patients have late checkups
		* 83.9% of Viral infection patients have early followups
		 """)

# |------------------------------------- QUERY - 14 -----------------------------------------------|
# Lab Supply Distribution According To Tests Conducted Over Years

with st.expander("Lab Supply Distribution According To Tests Conducted Over Years"):
	st.subheader("Lab Supply Distribution")
	st.write("Fetching medical tests conducted over years from Healthcare database using MYSQL Query")
	query14 = """
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
	"""

	df14 = pd.read_sql(query14, con=engine)
	st.dataframe(df14)

	fig14 = go.Figure()
	fig14.add_trace(go.Bar(x=df14['Years'],y= df14['BLOOD_TEST'],name='Blood test'))
	fig14.add_trace(go.Bar(x=df14['Years'],y= df14['MRI'],name='MRI'))
	fig14.add_trace(go.Bar(x=df14['Years'],y= df14['CT_SCAN'],name='CT Scan'))
	fig14.add_trace(go.Bar(x=df14['Years'],y= df14['X_RAY'],name='X Ray'))
	fig14.add_trace(go.Bar(x=df14['Years'],y= df14['ULTRASOUND'],name='Ultrasound'))
	
	fig14.update_layout(title='Requirements of lab test materials over years',
					 	xaxis=dict(title='Years',range=[2021,2025]),
						yaxis=dict(title='Lab Supplies',range=[0,1920]),
						barmode='group',
						template='plotly_white',
						height=1000)
	st.plotly_chart(fig14)
	st.subheader("Test Lab Supply Insights")
	st.markdown("""
		* Across the years, BLOOD TEST supplies are mostly needed irrespective of diagnosis.
		 """)

# |------------------------------------- QUERY - 15 -----------------------------------------------|
# Doctor-Wise Patient Recovery Time Analysis

with st.expander("Doctor-Wise Patient Recovery Time Analysis"):
	st.subheader("Doctor-Wise Patient Recovery Time Analysis")
	st.write("Fetching doctorwise patient recovery time data from Healthcare database using MYSQL Query")
	query15= """
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
	"""

	df15 = pd.read_sql(query15, con=engine)
	st.dataframe(df15)

	fig15 = px.scatter(df15,
						x='avg_recovery_days',
						y='doctor',
						title='Average Patient Recovery Time Analysis',
						color='doctor')
	st.plotly_chart(fig15)
	st.subheader("Recovery Insights")
	st.markdown("""
		* Shortest average patient recovery done by Dr.Mark Joy
		* Longest average patient recovery done by Dr.Niki Sharma
		* Mostly all doctor's patient recovery days fall into 8-8.6 days
		 """)

# |------------------------------------- QUERY - 16 -----------------------------------------------|
# Net Revenue Per Patient Over Years

with st.expander("Net Revenue Over Years"):
	st.subheader("Net Revenue per patient over Years")
	st.write("Fetching revenue data from Healthcare database using MYSQL Query")
	query16 = """
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
	"""
	df16 = pd.read_sql(query16, con=engine)
	st.dataframe(df16)

	fig16 = px.line(df16,
				 	x='Years',
					y='Net_Revenue',
					title='Net revenue over Years',
					markers=True)
	st.plotly_chart(fig16)

	st.subheader("Revenue Insights")
	st.markdown("""
		* Net revenue reached a peak of Rs.16 million in 2023.
		* Across all years, average revenue per patient is approximately Rs.2600.
		 """)