from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoAlertPresentException
import datetime
import traceback
import csv
import time

from credentials import emails, passwords


def click_proceed_button(driver, timeout=15, label=""):
    try:
        proceed_button_xpath = '//input[@type="submit" and @name="proceed" and @value="Proceed"]'
        proceed_button = WebDriverWait(driver, timeout).until(
            EC.presence_of_element_located((By.XPATH, proceed_button_xpath))
        )
        driver.execute_script("arguments[0].scrollIntoView({behavior: 'auto', block: 'center'});", proceed_button)
        time.sleep(1)

        try:
            WebDriverWait(driver, timeout).until(EC.element_to_be_clickable((By.XPATH, proceed_button_xpath)))
            proceed_button.click()
        except:
            print(f"⚠️ Falling back to JS click for {label}")
            driver.execute_script("arguments[0].click();", proceed_button)

        print(f"✅ Clicked Proceed button {label}")

        time.sleep(2)
        if "Code: 500" in driver.page_source or "something went wrong" in driver.page_source:
            print(f"❌ 500 Error detected after {label}")
            return False

        return True

    except Exception as e:
        print(f"❌ Failed to click Proceed button {label}: {e}")
        traceback.print_exc()
        return False


# Setup log file
current_time = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
log_filename = f"vat_submission_log_{current_time}.csv"
submission_logs = []

# Year ranges to process
year_ranges = ["2025-04-21---2025-05-21"]

# Loop through all credentials
for email, password in zip(emails, passwords):
    driver = webdriver.Chrome()
    driver.get('https://taxpromax.firs.gov.ng/taxpayer/login')
    try:
        driver.find_element(By.NAME, 'email').send_keys(email)
        driver.find_element(By.NAME, 'password').send_keys(password)
        driver.find_element(By.XPATH, '//button[@type="submit"]').click()
        WebDriverWait(driver, 10).until(EC.url_contains("taxpayer"))
        print(f"🔐 Logged in successfully as {email}")

        driver.get('https://taxpromax.firs.gov.ng/taxpayer/pending')

        for year in year_ranges:
            try:
                row_xpath = f"//tr[td[1][normalize-space()='VAT'] and td[4][contains(text(), '{year}')]]"
                row = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, row_xpath)))
                assessment_number = row.find_element(By.XPATH, "./td[3]").text.strip()
                print(f"📄 Found Assessment Number for {year}: {assessment_number}")

                driver.get(f"https://taxpromax.firs.gov.ng/taxpayer/schv0?id={assessment_number}")
                print("📄 Navigated to Sales Schedule")

                try:
                    currency_option = WebDriverWait(driver, 5).until(
                        EC.presence_of_element_located((By.XPATH, '//input[@name="currency" and @value="NGN"]'))
                    )
                    if not currency_option.is_selected():
                        currency_option.click()
                        print("💱 Selected NGN currency")
                    else:
                        print("💱 NGN already selected")
                except:
                    print("⚠️ NGN currency selection failed or already hidden")

                if not click_proceed_button(driver, label="after NGN currency"):
                    submission_logs.append([email, "Failure", "500 error after first Proceed"])
                    break

                if not click_proceed_button(driver, label="on Purchases page"):
                    submission_logs.append([email, "Failure", "500 error on Purchases page"])
                    break

                if not click_proceed_button(driver, label="on third page (post-purchases)"):
                    submission_logs.append([email, "Failure", "500 error on third page"])
                    break

                driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(1)

                vat_value = 0.0  # You may later extract this from the VAT box field if needed

                declared_checkbox = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.NAME, "declaration"))
                )
                driver.execute_script("arguments[0].scrollIntoView(true);", declared_checkbox)
                time.sleep(1)

                if not declared_checkbox.is_selected():
                    try:
                        WebDriverWait(driver, 5).until(EC.element_to_be_clickable((By.NAME, "declaration")))
                        declared_checkbox.click()
                    except:
                        driver.execute_script("arguments[0].click();", declared_checkbox)

                    try:
                        WebDriverWait(driver, 5).until(EC.alert_is_present())
                        alert = driver.switch_to.alert
                        alert_text = alert.text.strip()
                        print(f"📢 Alert: {alert_text}")
                        if "NGN 0" in alert_text or "NGN       0" in alert_text:
                            alert.accept()
                    except (TimeoutException, NoAlertPresentException):
                        print("⚠️ No alert after checkbox")

                if declared_checkbox.is_selected():
                    print("☑️ Declaration checkbox selected")

                submit_button = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((By.XPATH,
                        '//button[contains(text(), "Submit")] | //input[@type="submit" and contains(@value, "Submit")]'))
                )
                submit_button.click()
                print("🚀 Clicked Submit button")

                try:
                    WebDriverWait(driver, 5).until(EC.alert_is_present())
                    alert = driver.switch_to.alert
                    alert_text = alert.text.strip()
                    print(f"📢 Alert says: {alert_text}")
                    if "NGN 0" in alert_text.upper() and float(vat_value) == 0.0:
                        alert.accept()
                        print("✅ Alert confirmed and accepted")
                except (TimeoutException, NoAlertPresentException):
                    print("⚠️ No alert to handle")

                submission_logs.append([email, "Success", "Submitted successfully"])

            except Exception as inner_e:
                print(f"❌ Failed to process year {year}: {inner_e}")
                submission_logs.append([email, "Failure", f"Submission error: {inner_e}"])
                traceback.print_exc()

    except Exception as login_error:
        print(f"❌ Login or process error for {email}: {login_error}")
        submission_logs.append([email, "Failure", f"Login error: {login_error}"])
        traceback.print_exc()
    finally:
        try:
            driver.get('https://taxpromax.firs.gov.ng/logout')
            driver.quit()
            print(f"🚪 Logged out and closed browser for {email}")
        except Exception as e:
            print(f"⚠️ Error during logout/cleanup: {e}")

# Write log file
with open(log_filename, mode='w', newline='') as file:
    writer = csv.writer(file)
    writer.writerow(["Email", "Status", "Reason"])
    writer.writerows(submission_logs)

print(f"📝 Log written to {log_filename}")
