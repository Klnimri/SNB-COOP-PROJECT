import streamlit as st
import pandas as pd
import time
import requests
import os
from datetime import datetime
import pyodbc

st.set_page_config(
page_title="SNB",
page_icon=(r"/Users/klnimri/Desktop/Newtest/Test/bin/SNB_ICON.png"), 
layout="centered",
initial_sidebar_state="expanded"
)

def connect_to_db():
    try:
        conn = pyodbc.connect(
            'Driver={ODBC Driver 17 for SQL Server};'
            'Server=localhost;'  # Replace with your server name or IP address
            'Database=COOP;'  # Replace with your database name
            'UID=SA;'  # SQL Server username
            'PWD=Coop123456;'  # SQL Server password
        )
        return conn
    except pyodbc.Error as e:
        st.error(f"Error connecting to the database: {e}")
        return None

def authenticate_user(user_type, username, password):
    """
    Authenticate a user based on user type (Customer or Employee) and predefined credentials.
    
    Args:
        user_type (str): The type of user, either "Customer" or "Employee".
        username (str): The username (ID_Iqama_Num for Customer, Emp_ID for Employee).
        password (str): The password for authentication (predefined).

    Returns:
        tuple: The user's record if authentication is successful; otherwise, None.
    """
    conn = connect_to_db()
    cursor = conn.cursor()

    try:
        if user_type == "Customer":
            # Authenticate as a customer
            predefined_password = "customerpass"  # Predefined password for customers
            if password == predefined_password:
                customer_query = """
                SELECT ID_Iqama_Num, First_Name, Last_Name, Customer_Type
                FROM Customer
                WHERE ID_Iqama_Num = ?
                """
                cursor.execute(customer_query, (username,))
                customer = cursor.fetchone()
                return customer  # Returns customer record if found
            else:
                return None  # Password mismatch

        elif user_type == "Employee":
            # Authenticate as an employee
            manager_password = "managerpass"  # Predefined password for managers and administrators
            agent_password = "employeepass"  # Predefined password for agents

            # Fetch employee details from the database
            employee_query = """
            SELECT Emp_ID, First_Name, Last_Name, Emp_Role
            FROM Employee
            WHERE Emp_ID = ?
            """
            cursor.execute(employee_query, (username,))
            employee = cursor.fetchone()

            if employee:
                emp_id, first_name, last_name, emp_role = employee
                # Validate the password based on the role
                if emp_role in ["Manager", "Administrator"] and password == manager_password:
                    return employee  # Successful authentication for manager/administrator
                elif emp_role == "Agent" and password == agent_password:
                    return employee  # Successful authentication for agent
                else:
                    return None  # Password mismatch or invalid role
            else:
                return None  # Employee not found
        else:
            return None  # Invalid user type

    except Exception as e:
        st.error(f"Error during authentication: {e}")
        return None
    finally:
        conn.close()

def login_page():
    # Add custom styling and an image at the top
    customize_login_page()
    st.markdown(
        """
        <style>
        .center-title {
            display: flex;
            justify-content: center;
            align-items: center;
            height: 50px;
            font-size: 36px;
            font-weight: bold;
            color: #084C3C;
        }
        </style>
        <div class="center-title">Login Page</div>
        """,
        unsafe_allow_html=True,
    )

    # Input fields for username and password
    user_type = st.radio("Select User Type", ["Customer", "Employee"])
    
    username_label = "ID Number / Iqama Number" if user_type == "Customer" else "Employee ID"
    username = st.text_input(username_label)
    password = st.text_input("Password", type="password")

    # Check login state
    if "login_success" not in st.session_state:
        st.session_state["login_success"] = False

    # Button styles
    st.markdown(
        """
        <style>
        div.stButton > button {
            background-color: #4CAF50 !important;
            color: white !important;
            border: none;
            padding: 10px 20px !important;
            font-size: 16px !important;
            font-weight: bold;
            cursor: pointer;
            border-radius: 4px !important;
            margin-top: 20px;
            box-shadow: 0px 4px 6px rgba(0, 0, 0, 0.1);
        }
        div.stButton > button:hover {
            background-color: #45a049 !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    # Login actions
    col1, col2, col3 = st.columns(3)

    with col1:  # First column for the Login button
        if st.button("Login"):
            if username.strip() and password.strip():
                # Authenticate user
                user = authenticate_user(user_type, username, password)
                if user:
                    st.session_state["user_type"] = user_type
                    st.session_state["logged_in"] = True
                    st.session_state["login_success"] = True

                    # Navigate based on user type
                    if user_type == "Customer":
                        st.session_state["customer_id"] = user[0] # Store ID_Iqama_Num
                        st.session_state["logged_in"] = True 
                        st.session_state["page"] = "Submit Ticket"  # Default page for customers
                        st.session_state["available_pages"] = [
                            "Submit Ticket",
                            "Check Ticket Status",
                            "FAQ Info Page"
                        ]
                        st.success("Logged in successfully as Customer")
                    elif user_type == "Employee":
                        conn = connect_to_db()
                        cursor = conn.cursor()
                        cursor.execute("SELECT Emp_Role FROM Employee WHERE Emp_ID = ?", (username,))
                        role_result = cursor.fetchone()

                        if role_result:
                            emp_role = role_result[0]
                            st.session_state["emp_id"] = username  # Store Emp_ID
                            if emp_role in ["Manager", "Administrator"]:
                                st.session_state["page"] = "Management Dashboard"
                                st.session_state["available_pages"] = [
                                    "Management Dashboard",
                                    "Ticket Dashboard",
                                    "Customer Dashboard",
                                ]
                                st.success("Logged in successfully as Manager/Administrator")
                            elif emp_role == "Agent":
                                st.session_state["page"] = "Respond to a Ticket"
                                st.session_state["available_pages"] = [
                                    "Respond to a Ticket",
                                    "Check Ticket Status",
                                ]
                                st.success("Logged in successfully as Agent")
                            else:
                                st.error("Invalid role. Please check your credentials.")
                        else:
                            st.error("Employee not found. Please check the Employee ID.")
                        conn.close()
                else:
                    st.error("Invalid username or password.")
            else:
                st.error("Please fill out all fields.")

    with col2:  # Second column for the Forget Password button
        if st.button("Forget Password"):
            st.session_state["page"] = "Forget Password"

    with col3:  # Third column for the Create Account button
        if st.button("Create an Account"):
            st.session_state["page"] = "Create Account"

def forget_password_page():
    # Page title and instructions
    st.markdown(
        '<h1 style="color: #084C3C; text-align: center;">Forget Password</h1>',
        unsafe_allow_html=True
    )
    st.markdown(
        '<p style="color: #084C3C; text-align: center;">Enter your username or email to reset your password.</p>',
        unsafe_allow_html=True
    )

    # Input field for username or email
    username_or_email = st.text_input("Username or Email", placeholder="Enter your username or email")

    # Custom button styling
    st.markdown(
        """
        <style>
        div.stButton > button {
            background-color: #4CAF50 !important;
            color: white !important;
            border: none !important;
            padding: 10px 20px !important;
            text-align: center !important;
            font-size: 16px !important;
            font-weight: bold !important;
            cursor: pointer !important;
            border-radius: 4px !important;
            transition: background-color 0.3s ease !important;
            margin-top: 10px !important;
            box-shadow: 0px 4px 6px rgba(0, 0, 0, 0.1) !important;
        }
        div.stButton > button:hover {
            background-color: #45a049 !important;
            color: white !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    # Function to check if username or email exists in the database
    def check_user_in_db(username_or_email):
        conn = connect_to_db()
        cursor = conn.cursor()

        try:
            # Check in the Customer table
            cursor.execute(
                "SELECT ID_Iqama_Num FROM dbo.Customer WHERE ID_Iqama_Num = ? OR Email = ?",
                (username_or_email, username_or_email)
            )
            customer_result = cursor.fetchone()

            # Check in the Employee table if not found in Customer
            if not customer_result:
                cursor.execute(
                    "SELECT Emp_ID FROM dbo.Employee WHERE Emp_ID = ? OR Email = ?",
                    (username_or_email, username_or_email)
                )
                employee_result = cursor.fetchone()
                return employee_result is not None

            return True
        except Exception as e:
            st.error(f"Error checking user in the database: {e}")
            return False
        finally:
            conn.close()

    # Reset Password button
    if st.button("Reset Password"):
        if username_or_email.strip():
            if check_user_in_db(username_or_email):
                st.success(f"A password reset link has been sent to {username_or_email}.")
            else:
                st.error("The username or email does not exist in our records. Please try again.")
        else:
            st.error("Please enter a valid username or email.")
    add_return_to_login()
    
def add_return_to_login():
    """
    A versatile function that logs out the user, clears session state, 
    hides the sidebar, and displays appropriate messages based on the current page.
    Can be used on any page (e.g., Create Account, Forget Password, Submit Ticket, etc.).
    """
    # Get the current page from session state
    current_page = st.session_state.get("page", "")

    # Add custom styling for the Back to Login button
    st.markdown(
        """
        <style>
        div.stButton > button {
            background-color: #4CAF50 !important; /* Green background */
            color: white !important; /* White text */
            border: none !important; /* No border */
            padding: 10px 20px !important; /* Button padding */
            text-align: center !important; /* Center the text */
            font-size: 16px !important; /* Font size */
            font-weight: bold !important; /* Bold text */
            cursor: pointer !important; /* Pointer cursor */
            border-radius: 4px !important; /* Rounded corners */
            transition: background-color 0.3s ease !important; /* Smooth hover effect */
            display: inline-block !important; /* Inline block display */
            margin-top: 20px !important; /* Space above the button */
            box-shadow: 0px 4px 6px rgba(0, 0, 0, 0.1) !important; /* Optional shadow */
        }
        div.stButton > button:hover {
            background-color: #45a049 !important; /* Slightly lighter green on hover */
            color: white !important; /* Keep text white on hover */
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    # Handle different behaviors based on the current page
    if current_page in ["Create Account", "Forget Password"]:
        if st.button("Back to Login"):
            # Clear session state (logout user)
            for key in list(st.session_state.keys()):
                del st.session_state[key]

            # Display navigation info
            st.info("Navigating back to the Login page.")

            # Hide sidebar for a cleaner UI
            hide_sidebar()

            # Stop execution to clear the page
            st.stop()
    else:
        # Standard logout behavior for other pages
        if st.sidebar.button("Back to Login"):
            # Clear session state (logout user)
            for key in list(st.session_state.keys()):
                del st.session_state[key]

            # Display logout message
            st.warning("You have been logged out. Please log in again.")

            # Hide sidebar for a cleaner UI
            hide_sidebar()

            # Stop execution to clear the page
            st.stop()
           
def hide_sidebar():
    # Function to hide the sidebar
    st.markdown(
        """
        <style>
        section[data-testid="stSidebar"] {
            display: none; /* Hide the sidebar */
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

def main():

    # Initialize session state variables if they don't exist
    if "page" not in st.session_state:
        st.session_state["page"] = "Login"  # Default to the Login page
    if "available_pages" not in st.session_state:
        st.session_state["available_pages"] = []  # Default to no pages available
    if "logged_in" not in st.session_state:
        st.session_state["logged_in"] = False  # Default to not logged in
    if "user_type" not in st.session_state:
        st.session_state["user_type"] = None  # Default to no user type

    # Handle Login, Forget Password, and Create Account pages separately
    if st.session_state["page"] == "Login":
        login_page()
    elif st.session_state["page"] == "Forget Password":
        forget_password_page()
    elif st.session_state["page"] == "Create Account":
        create_account_page()
    else:
        # Check if the user is logged in
        if st.session_state["logged_in"]:
            # Display the navigation sidebar with the available pages
            st.sidebar.title("Navigation")
            page = st.sidebar.radio("Go to", st.session_state["available_pages"])
            st.session_state["page"] = page

            # Render the selected page based on the user's role and navigation
            if page == "Submit Ticket":
                submit_ticket_page()
            elif page == "Check Ticket Status":
                if st.session_state["user_type"] == "Customer":
                    check_ticket_status_page()
                else:
                    check_ticket_status_for_employee()
            elif page == "FAQ Info Page":
                faq_info_page()
            elif page == "Management Dashboard":
                management_dashboard_page()
            elif page == "Ticket Dashboard":
                ticket_dashboard_page()
            elif page == "Customer Dashboard":
                customer_dashboard_page()
            elif page == "Respond to a Ticket":
                respond_to_ticket_page()
            else:
                st.error("You do not have permission to access this page.")
        else:
            # If not logged in, redirect to the login page
            st.session_state["page"] = "Login"
            login_page()

def center_logo(logo_path="/Users/klnimri/Desktop/Newtest/Test/bin/logo.png", width=300):
    """
    Displays a centered logo on the page.

    Args:
        logo_path (str): Path to the logo image.
        width (int): Width of the logo.
    """
    # Create three columns for layout
    col1, col2, col3 = st.columns([1, 2, 1])  # Adjust column width ratios

    with col1:
        st.empty()  # Empty content in the first column

    with col2:
        try:
            # Display the logo image in the center column
            st.image(logo_path, width=width)
        except Exception as e:
            st.warning(f"Unable to load the logo. Error: {e}")

    with col3:
        st.empty()  # Empty content in the third column

def create_account_page():
    center_logo()
    vspace()
    vspace()
    vspace()
    hide_sidebar()

    st.markdown("<h1 style='text-align: center; color: #084C3C;'>Create Account</h1>", unsafe_allow_html=True)

    # Styling for buttons
    st.markdown(
        """
        <style>
        div.stButton > button {
            background-color: #4CAF50 !important;
            color: white !important;
            border: none !important;
            padding: 10px 20px !important;
            text-align: center !important;
            font-size: 16px !important;
            font-weight: bold !important;
            border-radius: 4px !important;
            box-shadow: 0px 4px 6px rgba(0, 0, 0, 0.1) !important;
            transition: background-color 0.3s ease !important;
        }
        div.stButton > button:hover {
            background-color: #45a049 !important;
            color: white !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    # Form for account creation
    with st.form(key="create_account_form"):
        id_number = st.text_input("ID Number / Iqama Number")
        first_name = st.text_input("First Name")
        second_name = st.text_input("Second Name")
        last_name = st.text_input("Last Name")
        nationality = st.selectbox("Nationality", get_country_list())
        email = st.text_input("E-mail")
        phone_number = st.text_input("Phone Number")
        dob = st.date_input("Date of Birth", min_value=datetime(1900, 1, 1), max_value=datetime.now())
        short_address = st.text_input(
            "Short Address Code (4 letters + 4 digits)",
            max_chars=8,
            help="Enter exactly 4 letters followed by 4 digits (e.g., ABCD1234)",
        )
        customer_type = st.selectbox("Customer Type", ["Retail", "Corporate"])

        submitted = st.form_submit_button("Create Account")
        
        if submitted:
            # Validate short address
            if validate_short_address(short_address):
                conn = connect_to_db()
                cursor = conn.cursor()
                try:
                    # Format DOB as string for database compatibility
                    dob_str = dob.strftime('%Y-%m-%d')  # Adjust format if required
                    query = """
                    INSERT INTO Customer (ID_Iqama_Num, First_Name, Second_Name, Last_Name, Nationality, Email, PhoneNumber, DOB, Customer_Type, Short_Address) 
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """
                    cursor.execute(
                        query,
                        (id_number, first_name, second_name, last_name, nationality, email, phone_number, dob_str, customer_type, short_address)
                    )
                    conn.commit()
                    st.success("Account created successfully!")
                except Exception as e:
                    st.error(f"Error creating account: {e}")
                finally:
                    conn.close()
            else:
                st.error("Invalid Short Address Code. It must be 4 letters followed by 4 digits (e.g., ABCD1234).")
    add_return_to_login()

def validate_short_address(short_address):
    return len(short_address) == 8 and short_address[:4].isalpha() and short_address[4:].isdigit()

def get_country_list():
    return [
        "Afghanistan", "Albania", "Algeria", "Andorra", "Angola", "Antigua and Barbuda", "Argentina", "Armenia",
        "Australia", "Austria", "Azerbaijan", "Bahamas", "Bahrain", "Bangladesh", "Barbados", "Belarus", "Belgium",
        "Belize", "Benin", "Bhutan", "Bolivia", "Bosnia and Herzegovina", "Botswana", "Brazil", "Brunei", "Bulgaria",
        "Burkina Faso", "Burundi", "Cabo Verde", "Cambodia", "Cameroon", "Canada", "Central African Republic", "Chad",
        "Chile", "China", "Colombia", "Comoros", "Congo (Congo-Brazzaville)", "Costa Rica", "Croatia", "Cuba", "Cyprus",
        "Czechia (Czech Republic)", "Denmark", "Djibouti", "Dominica", "Dominican Republic", "Ecuador", "Egypt",
        "El Salvador", "Equatorial Guinea", "Eritrea", "Estonia", "Eswatini", "Ethiopia", "Fiji", "Finland", "France",
        "Gabon", "Gambia", "Georgia", "Germany", "Ghana", "Greece", "Grenada", "Guatemala", "Guinea", "Guinea-Bissau",
        "Guyana", "Haiti", "Holy See", "Honduras", "Hungary", "Iceland", "India", "Indonesia", "Iran", "Iraq", "Ireland",
        "Israel", "Italy", "Jamaica", "Japan", "Jordan", "Kazakhstan", "Kenya", "Kiribati", "Korea (North)",
        "Korea (South)", "Kosovo", "Kuwait", "Kyrgyzstan", "Laos", "Latvia", "Lebanon", "Lesotho", "Liberia", "Libya",
        "Liechtenstein", "Lithuania", "Luxembourg", "Madagascar", "Malawi", "Malaysia", "Maldives", "Mali", "Malta",
        "Marshall Islands", "Mauritania", "Mauritius", "Mexico", "Micronesia", "Moldova", "Monaco", "Mongolia",
        "Montenegro", "Morocco", "Mozambique", "Myanmar", "Namibia", "Nauru", "Nepal", "Netherlands", "New Zealand",
        "Nicaragua", "Niger", "Nigeria", "North Macedonia", "Norway", "Oman", "Pakistan", "Palau", "Palestine State",
        "Panama", "Papua New Guinea", "Paraguay", "Peru", "Philippines", "Poland", "Portugal", "Qatar", "Romania",
        "Russia", "Rwanda", "Saint Kitts and Nevis", "Saint Lucia", "Saint Vincent and the Grenadines", "Samoa",
        "San Marino", "Sao Tome and Principe", "Saudi Arabia", "Senegal", "Serbia", "Seychelles", "Sierra Leone",
        "Singapore", "Slovakia", "Slovenia", "Solomon Islands", "Somalia", "South Africa", "South Sudan", "Spain",
        "Sri Lanka", "Sudan", "Suriname", "Sweden", "Switzerland", "Syria", "Tajikistan", "Tanzania", "Thailand",
        "Timor-Leste", "Togo", "Tonga", "Trinidad and Tobago", "Tunisia", "Turkey", "Turkmenistan", "Tuvalu", "Uganda",
        "Ukraine", "United Arab Emirates", "United Kingdom", "United States", "Uruguay", "Uzbekistan", "Vanuatu",
        "Venezuela", "Vietnam", "Yemen", "Zambia", "Zimbabwe"
    ]

def create_customer_account(id_number, first_name, second_name, last_name, nationality, email, phone_number, dob, short_address):
    conn = connect_to_db()
    cursor = conn.cursor()
    query = """
    INSERT INTO dbo.Customer (ID_Iqama_Num, First_Name, Second_Name, Last_Name, Nationality, Email, PhoneNumber, DOB, Short_Address)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """
    cursor.execute(query, (id_number, first_name, second_name, last_name, nationality, email, phone_number, dob, short_address))
    conn.commit()
    conn.close()

def submit_ticket_page():
    add_return_to_login()
    center_logo()
    vspace()
    vspace()
    vspace()
    vspace()
    st.markdown('<h1 style="color: #084C3C;">Submit a Ticket</h1>', unsafe_allow_html=True)
    st.markdown('<p style="color: #084C3C;">Please fill out the form below to submit a ticket.</p>', unsafe_allow_html=True)
    
    customer_id = st.session_state.get("customer_id", "")
    
    with st.form(key="submit_ticket_form"):
        customer_id = st.text_input("Customer ID (ID_Iqama_Num)", value=customer_id)
        ticket_type = st.selectbox("Ticket Type", ["General", "Billing", "Technical"])
        ticket_subject = st.text_input("Ticket Subject")
        ticket_description = st.text_area("Describe your issue/request")

        submitted = st.form_submit_button("Submit")

        if submitted:
            if customer_id.strip() and ticket_description.strip():
                conn = connect_to_db()
                cursor = conn.cursor()
                try:
                    # Map TicketType to Priority
                    ticket_priority_mapping = {
                        "General": "Low",
                        "Billing": "High",
                        "Technical": "Medium",
                    }
                    ticket_priority = ticket_priority_mapping.get(ticket_type, "Low")  # Default to "Low" if not found

                    # Auto-assign Employee ID based on the Ticket Type
                    department_mapping = {
                        "General": "Customer Support",
                        "Billing": "Billing",
                        "Technical": "Technical Support",
                    }
                    selected_department = department_mapping[ticket_type]

                    # Get an available employee from the relevant department
                    cursor.execute(
                        """
                        SELECT TOP 1 Emp_ID 
                        FROM Employee 
                        WHERE Department = ? 
                        ORDER BY NEWID()
                        """,
                        (selected_department,)
                    )
                    employee = cursor.fetchone()
                    emp_id = employee[0] if employee else None

                    if emp_id is None:
                        st.error("No available employees in the selected department.")
                        return

                    # Format the current date as a string for insertion
                    current_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")  # Adjust format if needed

                    # Insert the new ticket into the database
                    insert_query = """
                    INSERT INTO Ticket (ID_Iqama_Num, Emp_ID, DateOfRequest, TicketPriority, 
                    TicketType, TicketSubject, TicketDescription, TicketStatus) 
                    VALUES (?, ?, ?, ?, ?, ?, ?, 'Pending')
                    """
                    cursor.execute(
                        insert_query,
                        (customer_id, emp_id, current_date, ticket_priority, ticket_type, ticket_subject, ticket_description),
                    )
                    conn.commit()

                    # Display success message with ticket and employee details
                    st.success(f"Your ticket has been submitted successfully! Assigned Employee ID: {emp_id or 'Unassigned'} with priority: {ticket_priority}")
                except Exception as e:
                    st.error(f"Error submitting ticket: {e}")
                    print(f"SQL Error: {e}")  # Debugging
                finally:
                    conn.close()
            else:
                st.error("Please fill out all required fields.")

def check_ticket_status_page():
    add_return_to_login()
    center_logo()
    vspace()
    vspace()
    vspace()
    vspace()
    st.markdown('<h1 style="color: #084C3C;">Check Ticket Status</h1>', unsafe_allow_html=True)
    st.markdown('<p style="color: #084C3C;">Enter your Customer ID (ID_Iqama_Num) to view your tickets.</p>', unsafe_allow_html=True)

    customer_id = st.session_state.get("customer_id", "")  # Get customer ID from session state

    # Input field for Customer ID
    customer_id = st.text_input("Customer ID (ID_Iqama_Num)", value=customer_id)

    # Check ticket status functionality
    if st.button("Check Status"):
        if customer_id.strip():
            conn = connect_to_db()
            cursor = conn.cursor()
            try:
                # SQL query to fetch ticket details for the given ID_Iqama_Num
                query = """
                SELECT 
                    Ticket_ID, 
                    DateOfRequest, 
                    TicketType, 
                    TicketSubject, 
                    TicketDescription, 
                    TicketStatus
                FROM Ticket
                WHERE ID_Iqama_Num = ?
                """
                cursor.execute(query, (customer_id,))
                tickets = cursor.fetchall()

                if tickets:
                    # Unpack each row to ensure individual columns are processed correctly
                    ticket_data = [list(ticket) for ticket in tickets]  # Convert tuples to lists

                    # Create DataFrame from the unpacked data
                    df = pd.DataFrame(ticket_data, columns=[
                        "Ticket ID", 
                        "Date of Request", 
                        "Ticket Type", 
                        "Ticket Subject", 
                        "Ticket Description", 
                        "Ticket Status"
                    ])
                    st.success(f"Displaying tickets for Customer ID: {customer_id}")
                    st.dataframe(df, use_container_width=True)
                else:
                    st.warning("No tickets found for the provided Customer ID.")
            except Exception as e:
                st.error(f"Error retrieving tickets: {e}")
            finally:
                conn.close()
        else:
            st.error("Please enter your Customer ID.")

def check_ticket_status_for_employee():
    add_return_to_login()
    center_logo()
    vspace()
    vspace()
    vspace()
    vspace()
    st.markdown('<h1 style="color: #084C3C;">Check Ticket Status (Employee View)</h1>', unsafe_allow_html=True)
    st.markdown('<p style="color: #084C3C;">Select or enter a Customer ID (ID_Iqama_Num) to view their tickets.</p>', unsafe_allow_html=True)

    conn = connect_to_db()
    cursor = conn.cursor()

    try:
        # Fetch list of customers for dropdown
        cursor.execute("SELECT ID_Iqama_Num, First_Name + ' ' + Last_Name AS FullName FROM Customer")
        customers = cursor.fetchall()
        customer_dict = {f"{row[1]} (ID: {row[0]})": row[0] for row in customers}  # {Display Name: ID}

        # Dropdown for selecting a customer
        selected_customer = st.selectbox("Select a Customer", list(customer_dict.keys()), index=0)

        # Text input for manually entering a Customer ID
        manual_customer_id = st.text_input("Or Enter Customer ID (ID_Iqama_Num) Manually")

        # Determine the final Customer ID
        customer_id = manual_customer_id.strip() if manual_customer_id.strip() else customer_dict[selected_customer]

        # Check ticket status
        if st.button("Check Status"):
            if customer_id:
                query = """
                SELECT 
                    Ticket_ID, 
                    DateOfRequest, 
                    TicketType, 
                    TicketSubject, 
                    TicketDescription, 
                    TicketStatus
                FROM Ticket
                WHERE ID_Iqama_Num = ?
                """
                cursor.execute(query, (customer_id,))
                tickets = cursor.fetchall()

                if tickets:
                    # Ensure data is properly structured
                    ticket_data = [list(ticket) for ticket in tickets]  # Convert each tuple to a list
                    
                    # Convert result into a DataFrame
                    df = pd.DataFrame(ticket_data, columns=[
                        "Ticket ID", "Date of Request", "Ticket Type", "Ticket Subject", "Ticket Description", "Ticket Status"
                    ])

                    st.success(f"Displaying tickets for Customer ID: {customer_id}")
                    st.markdown(
                                """
                                <style>
                                div[data-testid="stDataFrameContainer"] {
                                    width: 100% !important;
                                    height: 700px !important;
                                }
                                div[data-testid="stDataFrameContainer"] table {
                                    font-size: 16px !important;
                                }
                                </style>
                                """,
                                unsafe_allow_html=True
                            )
                    st.data_editor(df, use_container_width=True, height=250)

                else:
                    st.warning("No tickets found for the selected Customer ID.")
            else:
                st.error("Please enter or select a valid Customer ID.")

    except Exception as e:
        st.error(f"Error retrieving tickets: {e}")

    finally:
        conn.close()

def faq_info_page():
    add_return_to_login()
    center_logo()
    vspace()
    vspace()
    vspace()
    vspace()
    st.markdown('<h1 style="color: #084C3C;">FAQ & Information</h1>', unsafe_allow_html=True)

    faq_data = [
        ("How to open a new account?", "Visit your nearest branch with your ID or use our app for easy online account opening."),
        ("Branch Operating Hours", "Sunday to Thursday, 9:00 AM to 4:00 PM. Please check your nearest branch for details."),
        ("Update Personal Information", "You can update your information at a branch or through our app under 'Update Data'."),
        ("Technical Support", "Ensure your app is updated and your device is connected to the internet. If issues persist, contact our support.")
    ]

    for question, answer in faq_data:
        st.markdown(f'<h2 style="color: #084C3C;">{question}</h2>', unsafe_allow_html=True)
        st.markdown(f'<p style="color: #084C3C;">{answer}</p>', unsafe_allow_html=True)

def respond_to_ticket_page():
    add_return_to_login()
    # Add logo and title
    center_logo()
    vspace()
    vspace()
    vspace()
    vspace()
    st.markdown('<h1 style="color: #084C3C;">Respond to a Ticket</h1>', unsafe_allow_html=True)

    # Get employee ID from session state
    emp_id = st.session_state.get("emp_id")  # Assuming the employee ID is stored as 'emp_id'

    if not emp_id:
        st.error("Employee ID not found. Please log in again.")
        return

    # Connect to the database
    conn = connect_to_db()
    cursor = conn.cursor()

    try:
        # Query to fetch tickets and responses with status "Pending" or "In Progress"
        query = """
        SELECT 
    Ticket.Ticket_ID, 
    Ticket.ID_Iqama_Num AS Customer_ID, 
    Ticket.DateOfRequest AS Date, 
    Ticket.TicketType AS Type, 
    Ticket.TicketStatus AS Status, 
    COALESCE(Response.Response, 'No Response') AS Response, 
    COALESCE(Response.ResponseTime, 'None') AS ResponseTime
FROM Ticket
LEFT JOIN Response ON Ticket.Ticket_ID = Response.Ticket_ID
WHERE Ticket.TicketStatus IN ('Pending', 'In Progress')

        """
        
        cursor.execute(query)
        tickets = cursor.fetchall()
        if tickets:
            # Convert the fetched data into a DataFrame
            ticket_data = [list(ticket) for ticket in tickets]  # Convert tuples to lists
            df = pd.DataFrame(ticket_data, columns=[
                "Ticket Number", "Customer ID", "Date", "Type", "Status", "Response", "Response Time"
            ])
            
            st.dataframe(df)

            # Dropdown to select a ticket
            ticket_to_respond = st.selectbox("Select a ticket to respond to:", df["Ticket Number"].tolist())
            
            # Text area for response
            response_text = st.text_area("Response:", placeholder="Write your response here...")

            # Button to submit the response
            if st.button("Respond to Ticket"):
                if response_text.strip():
                    try:
                        # Insert response into the Response table and update the ticket status
                        response_query = """
                        INSERT INTO Response (Ticket_ID, Emp_ID, Response, ResponseTime) 
                        VALUES (?, ?, ?, GETDATE())
                        """
                        cursor.execute(response_query, (ticket_to_respond, emp_id, response_text))
                        
                        # Update the status of the ticket to "Resolved"
                        update_query = """
                        UPDATE Ticket 
                        SET TicketStatus = 'Resolved' 
                        WHERE Ticket_ID = ?
                        """
                        cursor.execute(update_query, (ticket_to_respond,))
                        conn.commit()

                        st.success(f"Response for Ticket {ticket_to_respond} submitted successfully!")
                    except Exception as e:
                        st.error(f"Error submitting response: {e}")
                else:
                    st.error("Please write a response before submitting.")
        else:
            st.warning("No tickets available to respond to.")
    except Exception as e:
        st.error(f"Error fetching tickets: {e}")
    finally:
        conn.close()

def employee_ticket_status_page():
    add_return_to_login()
    # Add logo and title
    center_logo()
    vspace()
    vspace()
    vspace()
    vspace()
    st.markdown('<h1 style="color: #084C3C;">Ticket Status</h1>', unsafe_allow_html=True)

    # Input field for Customer ID
    customer_id = st.text_input("Customer ID (ID_Iqama_Num)", help="Enter the Customer ID (ID_Iqama_Num) to check ticket statuses.")

    # Add custom styling for the "Check Ticket Status" button
    st.markdown(
        """
        <style>
        div.stButton > button {
            background-color: #4CAF50 !important;
            color: white !important;
            border: none !important;
            padding: 10px 20px !important;
            text-align: center !important;
            font-size: 16px !important;
            font-weight: bold !important;
            cursor: pointer !important;
            border-radius: 4px !important;
            transition: background-color 0.3s ease;
            display: inline-block;
            margin-top: 20px !important; /* Space above the button */
            box-shadow: 0px 4px 6px rgba(0, 0, 0, 0.1) !important; /* Optional shadow */
        }
        div.stButton > button:hover {
            background-color: #45a049 !important;
            color: white !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    # Check ticket status functionality
    if st.button("Check Ticket Status"):
        if customer_id.strip():
            conn = connect_to_db()
            cursor = conn.cursor()
            try:
                # Query to fetch tickets for the given Customer ID
                query = """
                SELECT Ticket_ID, TicketSubject, TicketStatus, DateOfRequest 
                FROM Ticket 
                WHERE ID_Iqama_Num = ?
                """
                cursor.execute(query, (customer_id,))
                tickets = cursor.fetchall()

                if tickets:
                    # Convert the result into a DataFrame for display
                    df = pd.DataFrame(tickets, columns=["Ticket Number", "Subject", "Status", "Date of Request"])
                    st.success(f"Displaying tickets for Customer ID: {customer_id}")
                    st.dataframe(df, use_container_width=True)
                else:
                    st.warning("No tickets found for the provided Customer ID.")
            except Exception as e:
                st.error(f"Error retrieving ticket status: {e}")
            finally:
                conn.close()
        else:
            st.error("Please enter your Customer ID (ID_Iqama_Num).")

def ticket_dashboard_page():
    add_return_to_login()
    center_logo()
    vspace()
    vspace()
    vspace()
    vspace()
    st.markdown('<h1 style="color: #084C3C;">Ticket Dashboard</h1>', unsafe_allow_html=True)

    # Connect to the database
    conn = connect_to_db()
    cursor = conn.cursor()

    try:
        # Fetch ticket data from the database
        ticket_query = """
        SELECT Ticket_ID, TicketType, TicketStatus, Emp_ID
        FROM Ticket
        WHERE TicketStatus IN ('Pending', 'In Progress')
        """
        cursor.execute(ticket_query)
        tickets = cursor.fetchall()

        if tickets:
            # Convert ticket data into a DataFrame
            ticket_data = [list(ticket) for ticket in tickets]
            df_tickets = pd.DataFrame(ticket_data, columns=["Ticket Number", "Type", "Status", "Assigned To"])

            # Display the tickets overview
            st.markdown('<h2 style="color: #084C3C;">Tickets Overview</h2>', unsafe_allow_html=True)
            st.dataframe(df_tickets)

            # Reassignment section
            st.markdown('<h2 style="color: #084C3C;">Reassign a Ticket</h2>', unsafe_allow_html=True)

            # Dropdown to select a ticket for reassignment
            ticket_to_reassign = st.selectbox("Select a ticket to reassign:", df_tickets["Ticket Number"].tolist(), key="ticket_to_reassign")

            # Fetch employee data for reassignment
            employee_query = """
            SELECT Emp_ID, First_Name + ' ' + Last_Name AS Name, Department
            FROM Employee
            """
            cursor.execute(employee_query)
            employees = cursor.fetchall()

            if employees:
                # Convert employee data into a DataFrame
                employee_data = [list(employee) for employee in employees]
                df_employee = pd.DataFrame(employee_data, columns=["Employee ID", "Name", "Department"])

                # Option to select an employee by dropdown or enter Employee ID manually
                st.markdown('<p style="color: #084C3C;">Select an employee to assign the ticket:</p>', unsafe_allow_html=True)
                assign_option = st.radio("Choose assignment method:", ["Select from Dropdown", "Enter Employee ID"], key="assign_option")

                if assign_option == "Select from Dropdown":
                    # Dropdown list with Employee Full Name + Department
                    employee_dropdown = st.selectbox(
                        "Select an employee:",
                        df_employee.apply(
                            lambda row: f"{row['Name']} - {row['Department']} (ID: {row['Employee ID']})", axis=1
                        ),
                        key="employee_dropdown"
                    )
                    # Extract Employee ID from the selected dropdown value
                    selected_employee_id = employee_dropdown.split("(ID: ")[-1].strip(")")
                elif assign_option == "Enter Employee ID":
                    selected_employee_id = st.text_input("Enter Employee ID:", key="manual_employee_id")

                # Button to confirm reassignment
                if st.button("Reassign Ticket", key="reassign_button"):
                    if selected_employee_id.strip():
                        try:
                            # Update the ticket assignment in the database
                            update_query = """
                            UPDATE Ticket 
                            SET Emp_ID = ?, TicketStatus = 'In Progress' 
                            WHERE Ticket_ID = ?
                            """
                            cursor.execute(update_query, (selected_employee_id, ticket_to_reassign))
                            conn.commit()
                            st.success(f"Ticket {ticket_to_reassign} has been successfully reassigned to Employee ID: {selected_employee_id}.")
                        except Exception as e:
                            st.error(f"Error reassigning ticket: {e}")
                    else:
                        st.error("Please select or enter a valid Employee ID.")
            else:
                st.warning("No employees available for reassignment.")
        else:
            st.warning("No tickets available for reassignment.")

        # Add the Power BI dashboard iframe
        st.markdown('<h2 style="color: #084C3C;">Dashboard Insights</h2>', unsafe_allow_html=True)
        st.components.v1.iframe(
            "https://app.powerbi.com/view?r=eyJrIjoiMDEwNzA2YjUtNGY0MC00NTFjLTg1ZTctYTZlZjQzOTUwNWUxIiwidCI6ImI0NTNkOTFiLTZhYzEtNGI2MS1iOGI4LTVlNjVlNDIyMjMzZiIsImMiOjl9",
            height=800,
            width=1000,
            scrolling=True
        )

    except Exception as e:
        st.error(f"Error loading data: {e}")
    finally:
        conn.close()

def customer_dashboard_page():
    # Add return to login button
    add_return_to_login()

    # Add logo and vertical space
    center_logo()
    vspace()
    vspace()
    vspace()
    vspace()

    st.markdown('<h1 style="color: #084C3C;">Customer Dashboard</h1>', unsafe_allow_html=True)

    # Connect to the database
    conn = connect_to_db()
    cursor = conn.cursor()

    try:
        # Search for a specific customer
        st.markdown('<h2 style="color: #084C3C;">Search for a Customer</h2>', unsafe_allow_html=True)

        # Input field for Customer ID / Iqama Number
        search_customer_id = st.text_input("Enter Customer ID Number / Iqama Number:")

        # Button to search for customer details
        if st.button("Search"):
            if search_customer_id.strip():
                # Query to fetch customer details and statistics
                customer_query = """
                SELECT 
                    C.ID_Iqama_Num AS Customer_ID,
                    CONCAT(C.First_Name, ' ', C.Last_Name) AS Name,
                    C.Email,
                    C.Customer_Type,
                    COUNT(T.Ticket_ID) AS Total_Tickets
                FROM Customer C
                LEFT JOIN Ticket T ON C.ID_Iqama_Num = T.ID_Iqama_Num
                WHERE C.ID_Iqama_Num = ?
                GROUP BY C.ID_Iqama_Num, C.First_Name, C.Last_Name, C.Email, C.Customer_Type
                """
                cursor.execute(customer_query, (search_customer_id,))
                customer_row = cursor.fetchone()

                if customer_row:
                    # Ensure the query returns the correct number of columns
                    customer_columns = [
                        "Customer ID", "Name", "Email", "Customer Type",
                        "Total Tickets"
                    ]
                    df_customer = pd.DataFrame([list(customer_row)], columns=customer_columns)

                    st.markdown(f"<h3 style='color: #084C3C;'>Customer Details</h3>", unsafe_allow_html=True)
                    st.dataframe(df_customer, use_container_width=True)

                    # Query to fetch customer tickets
                    ticket_query = """
                    SELECT 
                        Ticket.Ticket_ID AS Ticket_ID, 
                        Ticket.DateOfRequest AS Date_Of_Request,
                        Ticket.TicketType AS Ticket_Type, 
                        Ticket.TicketSubject AS Subject, 
                        Ticket.TicketDescription AS Description, 
                        Ticket.TicketStatus AS Status
                    FROM Ticket
                    WHERE Ticket.ID_Iqama_Num = ?
                    """
                    cursor.execute(ticket_query, (search_customer_id,))
                    tickets = cursor.fetchall()

                    if tickets:
                        # Ensure data is properly structured
                        ticket_data = [list(ticket) for ticket in tickets]

                        # Convert result into a DataFrame
                        ticket_columns = [
                            "Ticket ID", "Date of Request", "Ticket Type",
                            "Subject", "Description", "Status"
                        ]
                        df_tickets = pd.DataFrame(ticket_data, columns=ticket_columns)

                        st.markdown(f"<h3 style='color: #084C3C;'>Tickets for {df_customer['Name'][0]}</h3>", unsafe_allow_html=True)
                        st.dataframe(df_tickets, use_container_width=True)
                    else:
                        st.warning("No tickets found for this customer.")
                else:
                    st.error("Customer not found. Please enter a valid ID Number / Iqama Number.")
            else:
                st.error("Please enter a valid Customer ID / Iqama Number.")

    except Exception as e:
        st.error(f"Error loading data: {e}")

    finally:
        conn.close()
        # Add Power BI Dashboard Insights at the top
    st.markdown('<h2 style="color: #084C3C;">Dashboard Insights</h2>', unsafe_allow_html=True)
    st.components.v1.iframe(
        "https://app.powerbi.com/view?r=eyJrIjoiOThhNGJkY2ItODUyZC00Y2UyLWJkYzQtYjdhZGVhOWI1ZWM5IiwidCI6ImI0NTNkOTFiLTZhYzEtNGI2MS1iOGI4LTVlNjVlNDIyMjMzZiIsImMiOjl9",
        height=800,
        width=1000,
        scrolling=True
    )

def management_dashboard_page():
    # Add return to login button
    add_return_to_login()

    # Center logo and add vertical space
    center_logo()
    vspace()
    vspace()
    vspace()
    vspace()

    st.markdown('<h1 style="color: #084C3C;">Management Dashboard</h1>', unsafe_allow_html=True)

    # Connect to the database
    conn = connect_to_db()
    cursor = conn.cursor()

    try:
        # Employee Overview Section
        st.markdown('<h2 style="color: #084C3C;">Employee Overview</h2>', unsafe_allow_html=True)

        # Query to fetch all employees
        overview_query = """
        SELECT Emp_ID, First_Name, Last_Name, Department
        FROM Employee
        """
        cursor.execute(overview_query)
        employees = cursor.fetchall()


        if employees:
            # Ensure rows are correctly split into multiple columns
            employee_data = [list(employee) for employee in employees]  # Convert tuples to lists

            # Convert employee data into a DataFrame
            df_employees = pd.DataFrame(
                employee_data,
                columns=["Employee ID", "First Name", "Last Name", "Department"]
            )
            st.dataframe(df_employees, use_container_width=True)
        else:
            st.warning("No employees found in the system.")

        # Search for a specific employee
        st.markdown('<h2 style="color: #084C3C;">Search for an Employee</h2>', unsafe_allow_html=True)

        search_type = st.radio("Search by:", ["Employee ID", "Dropdown"], horizontal=True)

        if search_type == "Employee ID":
            emp_id = st.text_input("Enter Employee ID:")
        else:
            # Dropdown selection
            cursor.execute("""
            SELECT Emp_ID, CONCAT(First_Name, ' ', Last_Name, ' - ', Department, ' (ID: ', Emp_ID, ')') AS Label
            FROM Employee
            """)
            dropdown_employees = cursor.fetchall()
            dropdown_options = {emp[1]: emp[0] for emp in dropdown_employees}  # {Label: ID}
            selected_label = st.selectbox("Select an employee:", list(dropdown_options.keys()))
            emp_id = dropdown_options[selected_label]

        if st.button("Search"):
            if emp_id:
                # Fetch employee details
                employee_query = """
                SELECT Emp_ID, First_Name, Last_Name, Department, Emp_Role
                FROM Employee
                WHERE Emp_ID = ?
                """
                cursor.execute(employee_query, (emp_id,))
                employee_details = cursor.fetchone()

                if employee_details:
                    emp_id, first_name, last_name, department, role = employee_details

                    # Display employee details
                    st.markdown(f"<h3 style='color: #084C3C;'>Details for Employee ID: {emp_id}</h3>", unsafe_allow_html=True)
                    st.markdown(f"**Name:** {first_name} {last_name}")
                    st.markdown(f"**Department:** {department}")
                    st.markdown(f"**Role:** {role}")

                    # Fetch employee tickets
                    ticket_query = """
                    SELECT 
                        Ticket.Ticket_ID, 
                        Ticket.ID_Iqama_Num, 
                        Ticket.DateOfRequest, 
                        Ticket.TicketPriority, 
                        Ticket.TicketType, 
                        Ticket.TicketSubject, 
                        Ticket.TicketDescription, 
                        Ticket.TicketStatus, 
                        Customer.First_Name + ' ' + Customer.Last_Name AS FullName, 
                        Customer.Email, 
                        Customer.Customer_Type
                    FROM Ticket
                    LEFT JOIN Response ON Ticket.Ticket_ID = Response.Ticket_ID
                    LEFT JOIN Customer ON Ticket.ID_Iqama_Num = Customer.ID_Iqama_Num
                    WHERE Ticket.Emp_ID = ?
                    """
                    cursor.execute(ticket_query, (emp_id,))
                    tickets = cursor.fetchall()

                    if tickets:
                        ticket_data = [list(ticket) for ticket in tickets]
                        df_tickets = pd.DataFrame(ticket_data, columns=[
                            "Ticket ID", "Customer ID", "Date of Request", "Priority", "Type",
                            "Subject", "Description", "Status", "Customer Name", "Customer Email", "Customer Type"
                        ])
                        st.markdown(f"<h3 style='color: #084C3C;'>Tickets assigned to Employee ID: {emp_id}</h3>", unsafe_allow_html=True)
                        st.dataframe(df_tickets, use_container_width=True)
                    else:
                        st.warning("No tickets found for this employee.")
                else:
                    st.error("Employee not found. Please enter a valid Employee ID.")
            else:
                st.error("Please enter a valid Employee ID.")

        # Add Power BI Dashboard Insights
        st.markdown('<h2 style="color: #084C3C;">Dashboard Insights</h2>', unsafe_allow_html=True)
        st.components.v1.iframe(
            "https://app.powerbi.com/view?r=eyJrIjoiNDJjOTRkMmQtOWE5Yi00NzJlLThkMzktMzk4MTVmODhlN2UxIiwidCI6ImI0NTNkOTFiLTZhYzEtNGI2MS1iOGI4LTVlNjVlNDIyMjMzZiIsImMiOjl9",
            height=800,
            width=1000,
            scrolling=True
        )

    except Exception as e:
        st.error(f"Error loading data: {e}")
    finally:
        conn.close()

def customize_navigation_menu_dark_green():
    st.markdown(
        """
        <style>
        /* Customize the navigation menu (sidebar) */
        section[data-testid="stSidebar"] {
            background-color: #084C3C !important; /* Set background to dark green */
        }
        section[data-testid="stSidebar"] p, 
        section[data-testid="stSidebar"] label, 
        section[data-testid="stSidebar"] h1, 
        section[data-testid="stSidebar"] h2, 
        section[data-testid="stSidebar"] h3, 
        section[data-testid="stSidebar"] div {
            color: white !important; /* Set text to white */
        }
        </style>
        """,
        unsafe_allow_html=True
    )

def customize_login_page():
    # Add custom CSS for styling
    st.markdown(
        """
        <style>
        .center-content {
            display: flex;
            justify-content: center;
            align-items: center;
            flex-direction: column;
            margin-top: 20px;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    # Use st.markdown to create a centered container for the image
    st.markdown('<div class="center-content">', unsafe_allow_html=True)
    
    # Display the image in the center
    center_logo()
    vspace()
    vspace()
    vspace()
    vspace()
 
def vspace():
    st.empty()
    st.text("")

def customize_submit_button():
    st.markdown(
        """
        <style>
        /* General styling for submit buttons */
        button[class^="css-"] {
            background-color: #084C3C !important; /* Dark green background */
            color: white !important; /* White text */
            border-radius: 10px !important; /* Rounded corners */
            padding: 10px 20px !important; /* Padding for the button */
            font-size: 16px !important; /* Ensure text size is visible */
            border: none !important; /* Remove border */
            box-shadow: 2px 2px 5px rgba(0, 0, 0, 0.2); /* Add subtle shadow */
        }
        button[class^="css-"]:hover {
            background-color: #056C4C !important; /* Slightly lighter green on hover */
            color: white !important; /* Keep text white on hover */
        }
        </style>
        """,
        unsafe_allow_html=True
    )

if __name__ == "__main__":
    customize_navigation_menu_dark_green()
    main()