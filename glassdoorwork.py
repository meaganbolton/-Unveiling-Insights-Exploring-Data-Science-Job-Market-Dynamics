import pandas as pd
import time
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# Initialize Chrome WebDriver
driver = webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()))
# Load Glassdoor login page
driver.get('https://www.glassdoor.com/profile/login_input.htm')
# Getting the email and password I will need to login
with open('email.txt', 'r') as f:
    email_login = f.read().strip()
with open('password.txt', 'r') as f:
    password_login = f.read().strip()

# 1st PAGE ENTER EMAIL AND MOVE ON #######################################
try:
    # Find the email input field and enter your email address
    email_input = driver.find_element(By.CLASS_NAME, 'email-input')

# # Within the email input field, find the input element
    email_input_field = email_input.find_element(By.TAG_NAME, 'input')
    # email_input = driver.find_element(By.NAME, 'username')
    email_input_field.send_keys(email_login)

    # Find the continue with email button and click it
    continue_with_email_button = driver.find_element(By.CLASS_NAME, 'emailButton')
    continue_with_email_button.click()
# 2ND PAGE ENTER PASSWORD AND LONGIN #########################################
    password_input = driver.find_element(By.ID, 'inlineUserPassword')
    password_input.send_keys(password_login)

    # Find the continue with email button and click it
    continue_with_signin_button = driver.find_element(By.CLASS_NAME, 'emailButton')
    continue_with_signin_button.click()

except NoSuchElementException as e:
    print("Element not found:", e)
except Exception as e:
    print("An error occurred:", e)

###############################################################
# Navigating to the pages I want to scrape
################################################################    

# Creating vectors to hold the information for my dataframe
titles = []
companies = []
cities = []
states = []
salaries = []
ratings = []
# Navigate to the job search page
driver.get('https://www.glassdoor.com/Job/jobs.htm')
# I searched popular data science locations so that I could pull information for those places specifically
# this is an array of those top locations (I also included my home town in this array)
locations = ['New York, NY', 'Houston, TX', 'San Francisco, CA', 'Seattle, WA', 'Chicago, IL', 'Raleigh, NC']
for k in range(len(locations)):
    # Enter job search criteria
    search_input = driver.find_element(By.ID, 'searchBar-jobTitle')
    search_input.send_keys('data science')

    location = driver.find_element(By.ID, 'searchBar-location')
    location.send_keys("")
    time.sleep(3)
    location.send_keys(locations[k])

    time.sleep(3)

    # #### I decided there wasn't enough information for each loaction without loading more job listings so this loop 
    # is for each time I click to show more job listings
    for i in range(2):
        jobs = driver.find_elements_by_css_selector('[data-test="jobListing"]')

        # #### loop through job posting and scrape data
        for job in jobs:
            # Extracting the job title
            title = job.find_element_by_css_selector('a.JobCard_jobTitle___7I6y').text
            titles.append(title)
            # Company
            company = job.find_element_by_css_selector('span.EmployerProfile_compactEmployerName__LE242').text
            companies.append(company)
            try:
                # Extract location
                location = job.find_element(By.CSS_SELECTOR, 'div.JobCard_location__rCz3x').text
                # Split location into city and state
                city, state = location.split(', ')
                cities.append(city)
                states.append(state)
            except (NoSuchElementException, ValueError):
                city = 'NA'
                state = 'NA'
                cities.append(city)
                states.append(state)

            try:
                # Extracting the salary if it is listed
                salary = job.find_element_by_css_selector('div.JobCard_salaryEstimate__arV5J').text
                salaries.append(salary)

            except:
                salary = 'NA'
                salaries.append(salary)

            try:
                # Extract company rating
                rating = job.find_element(By.CSS_SELECTOR, 'div.EmployerProfile_ratingContainer__ul0Ef').text
                ratings.append(rating)
            except NoSuchElementException:
                rating = 'NA'
                ratings.append(rating)
        
        # Find the "Show more jobs" button
        show_more_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, '//button[@data-test="load-more"]'))
        )
        show_more_button.click()
        time.sleep(3)

##################################################################################################################################################################3
# Combining all my vectors into one data set
data_jobs = {
    'Job Title': titles,
    'Company': companies,
    'City': cities,
    'State': states,
    'Salary': salaries,
    'Rating': ratings
}

# Create DataFrame
df_il_glassdoor = pd.DataFrame(data_jobs)
df_il_glassdoor.to_csv('df_all_glassdoor2.csv', index = False)

##############################################################################################################################
###########################################################################################
# After looking at the CSV I decided I wanted to make it easier to read and that I could organize the information better
# This is making the salary min and max for my data and just cleaning the dataframe to make it easier to work with
###########################################################################################
#############################################################################################################################
# I'm reading in the dataframe because this was done on a seperate day than the earlier code
df = pd.read_csv('C:/Users/meaga/df_glassdoor2.csv')
# Function to determine pay rate
def determine_pay_rate(salary):
    if isinstance(salary, str):
        if 'K' in salary:
            return 'Yearly'
        elif 'Per Hour' in salary:
            return 'Hourly'
        else:
            return 'NA'
    else:
        return 'NA'

# Apply the function to create the 'Pay rate' column
df['Pay rate'] = df['Salary'].apply(determine_pay_rate)

# Function to extract salary range
def extract_salary_range(salary):
    if isinstance(salary, str) and '-' in salary:
        salary_range = salary.split(' - ')
        salary_min = salary_range[0].replace('$', '').replace('K', '000').replace(' Per Hour', '').replace(',', '')
        salary_max = salary_range[1].replace('$', '').replace('K', '000').replace(' Per Hour', '').replace(',', '')
        return salary_min, salary_max
    elif isinstance(salary, float):
        return salary, salary
    else:
        salary_value = salary.replace('$', '').replace('K', '000').replace(' Per Hour', '').replace(',', '').replace(' (Employer est.)', '')
        return salary_value, salary_value

# Apply the function to create new columns
df['Salary_Min'], df['Salary_Max'] = zip(*df['Salary'].apply(extract_salary_range))


# Function to remove "(Employer est.)" from salary string
def remove_employer_est(salary):
    if isinstance(salary, str):
        salary = salary.replace(' (Employer est.)', '')
        salary = salary.replace(' (Glassdoor est.)', '')
        return salary
    else:
        return salary

# Apply the function to remove "(Employer est.)" from the Salary column
df['Salary_Max'] = df['Salary_Max'].apply(remove_employer_est)




# Function to extract estimate from salary string
def extract_estimate(salary):
    if isinstance(salary, str):
        if '(Employer est.)' in salary:
            return 'Employer'
        elif '(Glassdoor est.)' in salary:
            return 'Glassdoor'
        else:
            return 'NA'
    else:
        return 'NA'

# Apply the function to create the 'Estimate' column
df['Estimate'] = df['Salary'].apply(extract_estimate)
df.drop(columns=['Salary'], inplace=True)


# Display the updated DataFrame
print(df)
# writing the data to a new file 
df.to_csv('df_glassdoor.csv', index = False)