import streamlit as st
import sqlite3
import pandas as pd
from datetime import date, datetime
import hashlib
import io
import random

DB = "epfo_demo.db"

# =========================================================
# DATABASE
# =========================================================

def db():
    return sqlite3.connect(DB, check_same_thread=False)

def init_db():
    con = db()
    cur = con.cursor()

    cur.executescript("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE,
        password TEXT,
        role TEXT DEFAULT 'Employer',
        active INTEGER DEFAULT 1
    );

    CREATE TABLE IF NOT EXISTS establishments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        code TEXT UNIQUE,
        name TEXT,
        pan TEXT,
        address TEXT,
        state TEXT,
        district TEXT,
        pin TEXT,
        email TEXT,
        mobile TEXT,
        constitution TEXT,
        status TEXT DEFAULT 'Active'
    );

    CREATE TABLE IF NOT EXISTS employees (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        establishment_id INTEGER,
        member_id TEXT UNIQUE,
        uan TEXT,
        name TEXT,
        dob TEXT,
        gender TEXT,
        father_name TEXT,
        doj TEXT,
        doe TEXT,
        exit_reason TEXT,
        basic REAL DEFAULT 0,
        epf_wages REAL DEFAULT 0,
        eps_wages REAL DEFAULT 0,
        edli_wages REAL DEFAULT 0,
        status TEXT DEFAULT 'Active'
    );

    CREATE TABLE IF NOT EXISTS kyc (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        employee_id INTEGER,
        aadhaar TEXT,
        pan TEXT,
        bank TEXT,
        ifsc TEXT,
        status TEXT DEFAULT 'Pending'
    );

    CREATE TABLE IF NOT EXISTS payroll (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        employee_id INTEGER,
        month TEXT,
        basic REAL,
        epf_wages REAL,
        eps_wages REAL,
        edli_wages REAL,
        employee_share REAL,
        employer_share REAL,
        eps_share REAL,
        edli_share REAL,
        ncp REAL DEFAULT 0
    );

    CREATE TABLE IF NOT EXISTS ecr (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        month TEXT,
        members INTEGER,
        amount REAL,
        status TEXT DEFAULT 'Draft',
        trrn TEXT
    );

    CREATE TABLE IF NOT EXISTS ecr_errors (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        ecr_id INTEGER,
        employee_id INTEGER,
        error TEXT,
        status TEXT DEFAULT 'Open'
    );

    CREATE TABLE IF NOT EXISTS challans (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        trrn TEXT,
        amount REAL,
        status TEXT DEFAULT 'Unpaid',
        created_at TEXT
    );

    CREATE TABLE IF NOT EXISTS payments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        trrn TEXT,
        amount REAL,
        payment_ref TEXT,
        status TEXT,
        created_at TEXT
    );

    CREATE TABLE IF NOT EXISTS corrections (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        employee_id INTEGER,
        field_name TEXT,
        old_value TEXT,
        new_value TEXT,
        reason TEXT,
        status TEXT DEFAULT 'Pending',
        created_at TEXT
    );

    CREATE TABLE IF NOT EXISTS notices (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT,
        description TEXT,
        due_date TEXT,
        status TEXT DEFAULT 'Open',
        response TEXT
    );

    CREATE TABLE IF NOT EXISTS audit_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT,
        action TEXT,
        module TEXT,
        created_at TEXT
    );

    CREATE TABLE IF NOT EXISTS notifications (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        message TEXT,
        status TEXT DEFAULT 'Unread',
        created_at TEXT
    );
    """)

    # Demo login
    if not cur.execute(
        "SELECT id FROM users WHERE username='demoemployer'"
    ).fetchone():
        cur.execute(
            "INSERT INTO users(username,password,role) VALUES(?,?,?)",
            ("demoemployer", hash_password("demo123"), "Employer")
        )

    # Demo establishment
    if not cur.execute(
        "SELECT id FROM establishments WHERE code='DEMO001'"
    ).fetchone():
        cur.execute("""
        INSERT INTO establishments
        (code,name,pan,address,state,district,pin,email,mobile,constitution)
        VALUES (?,?,?,?,?,?,?,?,?,?)
        """, (
            "DEMO001",
            "ABC Technologies Pvt. Ltd. - DEMO",
            "ABCDE1234F",
            "Demo Industrial Area",
            "Haryana",
            "Gurugram",
            "122001",
            "demo@example.invalid",
            "9999999999",
            "Private Limited"
        ))

    con.commit()
    con.close()


def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()


def execute(sql, params=(), fetch=False):
    con = db()
    cur = con.cursor()
    cur.execute(sql, params)
    rows = cur.fetchall() if fetch else None
    con.commit()
    con.close()
    return rows


def log_action(action, module):
    execute("""
        INSERT INTO audit_logs(username,action,module,created_at)
        VALUES(?,?,?,?)
    """, (
        st.session_state.get("username", "demo"),
        action,
        module,
        datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    ))


# =========================================================
# LOGIN
# =========================================================

def login():
    st.markdown(
        """
        <div style="
        max-width:650px;
        margin:60px auto 20px auto;
        padding:30px;
        border-radius:15px;
        background:#ffffff;
        box-shadow:0 4px 20px rgba(0,0,0,.12);
        text-align:center;">
        <h1 style="color:#1261a0;">EPFO Employer</h1>
        <h3>Training / Demo Portal</h3>
        <p>Not an official EPFO website</p>
        </div>
        """,
        unsafe_allow_html=True
    )

    with st.form("login"):
        username = st.text_input("Employer User ID")
        password = st.text_input("Password", type="password")
        captcha = st.text_input("Demo Captcha", value="1234")

        submitted = st.form_submit_button("Sign In")

        if submitted:
            user = execute(
                "SELECT * FROM users WHERE username=? AND password=? AND active=1",
                (username, hash_password(password)),
                fetch=True
            )

            if user and captcha == "1234":
                st.session_state.logged = True
                st.session_state.username = username
                st.session_state.role = user[0][3]
                log_action("Login", "Authentication")
                st.rerun()
            else:
                st.error("Invalid demo credentials or captcha.")


# =========================================================
# HELPERS
# =========================================================

def header(title, subtitle=""):
    st.markdown(f"## {title}")
    if subtitle:
        st.caption(subtitle)


def status_badge(status):
    colors = {
        "Active": "#198754",
        "Approved": "#198754",
        "Paid": "#198754",
        "Success": "#198754",
        "Pending": "#fd7e14",
        "Open": "#dc3545",
        "Rejected": "#dc3545",
        "Failed": "#dc3545",
        "Draft": "#6c757d",
        "Unpaid": "#dc3545",
    }

    color = colors.get(status, "#6c757d")

    st.markdown(
        f"""
        <span style="
        background:{color};
        color:white;
        padding:4px 10px;
        border-radius:15px;
        font-size:12px;">
        {status}
        </span>
        """,
        unsafe_allow_html=True
    )


def employees_df():
    rows = execute("""
        SELECT id,member_id,uan,name,dob,doj,doe,basic,status
        FROM employees
        ORDER BY id DESC
    """, fetch=True)

    return pd.DataFrame(
        rows,
        columns=[
            "ID","Member ID","UAN","Name",
            "DOB","DOJ","DOE","Basic","Status"
        ]
    )


# =========================================================
# DASHBOARD
# =========================================================

def dashboard():
    header("🏠 Dashboard", "Employer overview")

    employees = execute(
        "SELECT COUNT(*) FROM employees",
        fetch=True
    )[0][0]

    active = execute(
        "SELECT COUNT(*) FROM employees WHERE status='Active'",
        fetch=True
    )[0][0]

    pending_kyc = execute(
        "SELECT COUNT(*) FROM kyc WHERE status='Pending'",
        fetch=True
    )[0][0]

    pending_ecr = execute(
        "SELECT COUNT(*) FROM ecr WHERE status!='Submitted'",
        fetch=True
    )[0][0]

    unpaid = execute(
        "SELECT COUNT(*) FROM challans WHERE status='Unpaid'",
        fetch=True
    )[0][0]

    c1,c2,c3,c4,c5 = st.columns(5)

    c1.metric("Total Members", employees)
    c2.metric("Active Members", active)
    c3.metric("KYC Pending", pending_kyc)
    c4.metric("ECR Pending", pending_ecr)
    c5.metric("Unpaid Challans", unpaid)

    st.divider()

    col1,col2 = st.columns(2)

    with col1:
        st.subheader("Alerts & To-Do")
        if pending_kyc:
            st.warning(f"{pending_kyc} KYC verification(s) pending.")
        if pending_ecr:
            st.warning(f"{pending_ecr} return(s) pending.")
        if unpaid:
            st.error(f"{unpaid} challan(s) unpaid.")
        if not any([pending_kyc,pending_ecr,unpaid]):
            st.success("No demo pending tasks.")

    with col2:
        st.subheader("Establishment")

        est = execute(
            "SELECT code,name,status FROM establishments LIMIT 1",
            fetch=True
        )

        if est:
            st.write("**Code:**", est[0][0])
            st.write("**Name:**", est[0][1])
            st.write("**Status:**", est[0][2])


# =========================================================
# ESTABLISHMENT
# =========================================================

def establishment():
    header("🏢 Establishment")

    tabs = st.tabs([
        "Profile",
        "Employer Details",
        "Authorized Signatory",
        "Bank Details",
        "Change Request"
    ])

    est = execute(
        "SELECT * FROM establishments WHERE code='DEMO001'",
        fetch=True
    )[0]

    with tabs[0]:
        st.subheader("Establishment Profile")

        with st.form("estprofile"):
            name = st.text_input("Establishment Name", est[2])
            pan = st.text_input("PAN", est[3])
            address = st.text_area("Address", est[4])
            state = st.text_input("State", est[5])
            district = st.text_input("District", est[6])
            pin = st.text_input("PIN", est[7])
            constitution = st.selectbox(
                "Constitution",
                ["Private Limited","Partnership","Proprietorship","LLP"],
                index=0
            )

            if st.form_submit_button("Save Profile"):
                execute("""
                    UPDATE establishments
                    SET name=?,pan=?,address=?,state=?,
                        district=?,pin=?,constitution=?
                    WHERE id=?
                """, (
                    name,pan,address,state,district,
                    pin,constitution,est[0]
                ))

                log_action("Update establishment profile","Establishment")
                st.success("Profile updated in demo database.")
                st.rerun()

    with tabs[1]:
        st.subheader("Employer / Contact")

        st.info(f"Email: {est[8]}")
        st.info(f"Mobile: {est[9]}")
        st.info(f"Establishment Code: {est[1]}")
        st.info(f"Status: {est[11]}")

    with tabs[2]:
        st.subheader("Authorized Signatory")

        name = st.text_input("Authorized Person")
        designation = st.text_input("Designation")
        email = st.text_input("Email")

        if st.button("Add Authorized Signatory"):
            if name:
                execute("""
                    INSERT INTO notifications(message,created_at)
                    VALUES(?,?)
                """, (
                    f"Authorized signatory '{name}' added — DEMO",
                    datetime.now().isoformat()
                ))
                log_action("Add authorized signatory","Establishment")
                st.success("Authorized signatory added in demo.")

    with tabs[3]:
        st.subheader("Bank Details — Demo")

        bank = st.selectbox(
            "Bank",
            ["Demo Bank","State Bank — Demo","HDFC — Demo","ICICI — Demo"]
        )
        account = st.text_input("Account Number — Demo", type="password")
        ifsc = st.text_input("IFSC — Demo")

        if st.button("Save Bank Details"):
            st.success("Bank details saved as demo data.")

    with tabs[4]:
        st.subheader("Profile Change Request")

        reason = st.text_area("Reason")
        if st.button("Submit Change Request"):
            if reason:
                execute("""
                    INSERT INTO corrections
                    (employee_id,field_name,old_value,new_value,reason,created_at)
                    VALUES(NULL,'ESTABLISHMENT','','',?,?)
                """, (
                    reason,
                    datetime.now().isoformat()
                ))
                st.success("Request submitted — DEMO.")


# =========================================================
# MEMBERS
# =========================================================

def members():
    header("👥 Member Management")

    tabs = st.tabs([
        "Member List",
        "Register Individual",
        "Register Bulk",
        "Approvals",
        "Member Search"
    ])

    with tabs[0]:
        df = employees_df()

        if len(df):
            st.dataframe(
                df,
                use_container_width=True,
                hide_index=True
            )

            selected = st.selectbox(
                "Select Employee",
                df["ID"].tolist()
            )

            if st.button("View Member"):
                employee_detail(selected)
        else:
            st.info("No members available.")

    with tabs[1]:
        add_employee()

    with tabs[2]:
        bulk_register()

    with tabs[3]:
        approvals()

    with tabs[4]:
        search_member()


def add_employee():
    st.subheader("Register - Individual")

    with st.form("employee_form"):

        name = st.text_input("Employee Name")
        dob = st.date_input(
            "Date of Birth",
            value=date(1995,1,1)
        )
        gender = st.selectbox(
            "Gender",
            ["Male","Female","Other"]
        )
        father = st.text_input("Father / Spouse Name")
        doj = st.date_input(
            "Date of Joining",
            value=date.today()
        )

        previous = st.radio(
            "Previous Employment?",
            ["No","Yes"]
        )

        existing_uan = ""
        if previous == "Yes":
            existing_uan = st.text_input(
                "Existing UAN — Demo"
            )

        basic = st.number_input(
            "Basic Wages",
            min_value=0.0,
            value=30000.0
        )

        submitted = st.form_submit_button(
            "Register Employee"
        )

        if submitted:

            if not name:
                st.error("Employee name required.")
                return

            # Demo UAN
            uan = existing_uan.strip()

            if not uan:
                uan = str(
                    random.randint(
                        100000000000,
                        999999999999
                    )
                )

            member_id = (
                "DEMO001"
                + str(
                    random.randint(
                        100000,
                        999999
                    )
                )
            )

            execute("""
                INSERT INTO employees
                (establishment_id,member_id,uan,name,dob,
                 gender,father_name,doj,basic,epf_wages,
                 eps_wages,edli_wages,status)
                VALUES(1,?,?,?,?,?,?,?,?,?,?,?,?)
            """, (
                member_id,
                uan,
                name,
                dob.isoformat(),
                gender,
                father,
                doj.isoformat(),
                basic,
                basic,
                basic,
                basic,
                "Active"
            ))

            log_action("Register employee","Member")

            st.success("Employee registered successfully.")
            st.info(f"Demo UAN: {uan}")
            st.info(f"Demo Member ID: {member_id}")


def bulk_register():
    st.subheader("Register - Bulk")

    template = pd.DataFrame({
        "name":["Rahul Sharma","Priya Verma"],
        "dob":["1995-01-01","1996-02-02"],
        "gender":["Male","Female"],
        "father_name":["Demo Father","Demo Father"],
        "doj":["2026-04-01","2026-04-01"],
        "basic":[30000,35000]
    })

    st.download_button(
        "Download Demo Template",
        template.to_csv(index=False),
        "employee_template.csv",
        "text/csv"
    )

    uploaded = st.file_uploader(
        "Upload CSV",
        type=["csv"]
    )

    if uploaded:

        df = pd.read_csv(uploaded)

        st.subheader("Preview")
        st.dataframe(df,use_container_width=True)

        required = [
            "name","dob","gender",
            "father_name","doj","basic"
        ]

        missing = [
            x for x in required
            if x not in df.columns
        ]

        if missing:
            st.error(
                "Missing columns: "
                + ", ".join(missing)
            )
        else:
            st.success(
                f"{len(df)} rows validated for demo."
            )

            if st.button("Create Demo Members"):
                count = 0

                for _,row in df.iterrows():

                    uan = str(
                        random.randint(
                            100000000000,
                            999999999999
                        )
                    )

                    member = (
                        "DEMO001"
                        + str(
                            random.randint(
                                100000,
                                999999
                            )
                        )
                    )

                    execute("""
                    INSERT INTO employees
                    (establishment_id,member_id,uan,name,
                     dob,gender,father_name,doj,basic,
                     epf_wages,eps_wages,edli_wages)
                    VALUES(1,?,?,?,?,?,?,?,?,?,?,?)
                    """,(
                        member,
                        uan,
                        str(row["name"]),
                        str(row["dob"]),
                        str(row["gender"]),
                        str(row["father_name"]),
                        str(row["doj"]),
                        float(row["basic"]),
                        float(row["basic"]),
                        float(row["basic"]),
                        float(row["basic"])
                    ))

                    count += 1

                log_action(
                    f"Bulk registered {count} members",
                    "Member"
                )

                st.success(
                    f"{count} demo members created."
                )


def search_member():
    st.subheader("Member Search")

    query = st.text_input(
        "Name / UAN / Member ID"
    )

    if query:
        rows = execute("""
            SELECT id,member_id,uan,name,doj,status
            FROM employees
            WHERE name LIKE ?
               OR uan LIKE ?
               OR member_id LIKE ?
        """, (
            f"%{query}%",
            f"%{query}%",
            f"%{query}%"
        ), fetch=True)

        df = pd.DataFrame(
            rows,
            columns=[
                "ID","Member ID","UAN",
                "Name","DOJ","Status"
            ]
        )

        st.dataframe(
            df,
            use_container_width=True,
            hide_index=True
        )


def employee_detail(employee_id):

    row = execute("""
        SELECT * FROM employees WHERE id=?
    """,(employee_id,),fetch=True)

    if not row:
        return

    e = row[0]

    st.subheader("Member Profile")

    c1,c2,c3 = st.columns(3)

    c1.metric("Member ID",e[2])
    c2.metric("UAN",e[3])
    c3.metric("Status",e[13])

    tabs = st.tabs([
        "Personal",
        "Employment",
        "UAN",
        "KYC",
        "Payroll",
        "Exit",
        "Correction",
        "History"
    ])

    with tabs[0]:
        st.write("**Name:**",e[4])
        st.write("**DOB:**",e[5])
        st.write("**Gender:**",e[6])
        st.write("**Father/Spouse:**",e[7])

    with tabs[1]:
        st.write("**DOJ:**",e[8])
        st.write("**DOE:**",e[9])
        st.write("**Basic:**",e[10])

    with tabs[2]:
        st.info(f"Demo UAN: {e[3]}")
        st.info("UAN status: Active — DEMO")

    with tabs[3]:
        k = execute("""
            SELECT aadhaar,pan,bank,ifsc,status
            FROM kyc WHERE employee_id=?
        """,(employee_id,),fetch=True)

        if k:
            st.write("Aadhaar:", mask(k[0][0]))
            st.write("PAN:", mask(k[0][1]))
            st.write("Bank:", mask(k[0][2]))
            st.write("IFSC:", k[0][3])
            status_badge(k[0][4])
        else:
            st.warning("KYC not submitted.")

    with tabs[4]:
        payroll_df(employee_id)

    with tabs[5]:
        exit_employee(employee_id)

    with tabs[6]:
        correction(employee_id)

    with tabs[7]:
        st.info("Audit/history available in Audit Trail.")


def mask(value):
    if not value:
        return "Not Available"
    value = str(value)
    return "*" * max(0,len(value)-4) + value[-4:]


# =========================================================
# KYC
# =========================================================

def kyc():
    header("🪪 KYC Management")

    employees = execute(
        "SELECT id,name,uan FROM employees",
        fetch=True
    )

    if not employees:
        st.info("Add an employee first.")
        return

    df = pd.DataFrame(
        employees,
        columns=["ID","Employee","UAN"]
    )

    st.dataframe(
        df,
        use_container_width=True,
        hide_index=True
    )

    selected = st.selectbox(
        "Employee",
        [(x[0],x[1]) for x in employees],
        format_func=lambda x:x[1]
    )[0]

    with st.form("kycform"):

        aadhaar = st.text_input(
            "Aadhaar — DEMO ONLY"
        )
        pan = st.text_input(
            "PAN — DEMO ONLY"
        )
        bank = st.text_input(
            "Bank Account — DEMO ONLY"
        )
        ifsc = st.text_input(
            "IFSC — DEMO"
        )

        submit = st.form_submit_button(
            "Submit KYC"
        )

        if submit:

            old = execute(
                "SELECT id FROM kyc WHERE employee_id=?",
                (selected,),
                fetch=True
            )

            if old:
                execute("""
                    UPDATE kyc
                    SET aadhaar=?,pan=?,bank=?,ifsc=?,
                        status='Pending'
                    WHERE employee_id=?
                """,(
                    aadhaar,pan,bank,ifsc,selected
                ))
            else:
                execute("""
                    INSERT INTO kyc
                    (employee_id,aadhaar,pan,bank,ifsc)
                    VALUES(?,?,?,?,?)
                """,(
                    selected,aadhaar,pan,bank,ifsc
                ))

            log_action("Submit KYC","KYC")

            st.success(
                "KYC submitted — DEMO status Pending."
            )

    st.divider()

    st.subheader("KYC Verification")

    pending = execute("""
        SELECT k.id,e.name,e.uan,k.status
        FROM kyc k
        JOIN employees e ON e.id=k.employee_id
        WHERE k.status='Pending'
    """,fetch=True)

    for k in pending:
        c1,c2,c3,c4 = st.columns(4)

        c1.write(k[1])
        c2.write(k[2])
        c3.write(k[3])

        if c4.button(
            "Approve",
            key=f"k{ k[0] }"
        ):
            execute(
                "UPDATE kyc SET status='Approved' WHERE id=?",
                (k[0],)
            )
            log_action("Approve KYC","KYC")
            st.rerun()


# =========================================================
# PAYROLL
# =========================================================

def payroll():
    header("💰 Payroll / Contribution")

    employees = execute("""
        SELECT id,name,basic
        FROM employees
        WHERE status='Active'
    """,fetch=True)

    if not employees:
        st.info("No active employees.")
        return

    month = st.text_input(
        "Wage Month",
        value=datetime.now().strftime("%Y-%m")
    )

    for e in employees:

        with st.expander(
            f"{e[1]} | Basic ₹{e[2]:,.2f}"
        ):

            basic = st.number_input(
                "Basic Wages",
                min_value=0.0,
                value=float(e[2]),
                key=f"basic_{e[0]}"
            )

            epf = st.number_input(
                "EPF Wages",
                min_value=0.0,
                value=float(e[2]),
                key=f"epf_{e[0]}"
            )

            eps = st.number_input(
                "EPS Wages",
                min_value=0.0,
                value=float(e[2]),
                key=f"eps_{e[0]}"
            )

            edli = st.number_input(
                "EDLI Wages",
                min_value=0.0,
                value=float(e[2]),
                key=f"edli_{e[0]}"
            )

            ncp = st.number_input(
                "NCP Days",
                min_value=0.0,
                value=0.0,
                key=f"ncp_{e[0]}"
            )

            emp_share, employer, eps_share, edli_share = calculate(
                epf,eps,edli
            )

            c1,c2,c3,c4 = st.columns(4)

            c1.metric(
                "Employee Share",
                f"₹{emp_share:,.2f}"
            )

            c2.metric(
                "Employer Share",
                f"₹{employer:,.2f}"
            )

            c3.metric(
                "EPS",
                f"₹{eps_share:,.2f}"
            )

            c4.metric(
                "EDLI",
                f"₹{edli_share:,.2f}"
            )

            if st.button(
                "Save Payroll",
                key=f"savepay_{e[0]}"
            ):

                execute("""
                INSERT INTO payroll
                (employee_id,month,basic,epf_wages,
                 eps_wages,edli_wages,employee_share,
                 employer_share,eps_share,edli_share,ncp)
                VALUES(?,?,?,?,?,?,?,?,?,?,?)
                """,(
                    e[0],month,basic,epf,eps,edli,
                    emp_share,employer,
                    eps_share,edli_share,ncp
                ))

                log_action(
                    f"Payroll saved for {e[1]}",
                    "Payroll"
                )

                st.success("Payroll saved.")


def calculate(epf,eps,edli):

    # TRAINING DEMO calculation.
    # Not a substitute for current EPFO statutory calculation.
    employee_share = round(epf * 0.12,2)

    eps_share = round(
        min(eps,15000) * 0.0833,
        2
    )

    employer = round(
        max(employee_share - eps_share,0),
        2
    )

    edli_share = round(
        min(edli,15000) * 0.005,
        2
    )

    return (
        employee_share,
        employer,
        eps_share,
        edli_share
    )


def payroll_df(employee_id):

    rows = execute("""
        SELECT month,basic,epf_wages,employee_share,
               employer_share,eps_share,edli_share,ncp
        FROM payroll
        WHERE employee_id=?
        ORDER BY id DESC
    """,(employee_id,),fetch=True)

    if rows:
        st.dataframe(
            pd.DataFrame(
                rows,
                columns=[
                    "Month","Basic","EPF Wages",
                    "Employee Share","Employer Share",
                    "EPS","EDLI","NCP"
                ]
            ),
            use_container_width=True,
            hide_index=True
        )
    else:
        st.info("No payroll records.")


# =========================================================
# ECR
# =========================================================

def ecr():
    header("📄 ECR / Return Filing")

    tabs = st.tabs([
        "Prepare ECR",
        "Validate",
        "Submit",
        "History",
        "Errors"
    ])

    with tabs[0]:
        month = st.text_input(
            "Wage Month",
            datetime.now().strftime("%Y-%m"),
            key="ecrmonth"
        )

        rows = execute("""
            SELECT COUNT(*),
                   COALESCE(SUM(employee_share+employer_share+
                                eps_share+edli_share),0)
            FROM payroll
            WHERE month=?
        """,(month,),fetch=True)[0]

        st.metric("Payroll Members",rows[0])
        st.metric("Contribution Amount",f"₹{rows[1]:,.2f}")

        if st.button("Create ECR Draft"):

            execute("""
                INSERT INTO ecr(month,members,amount,status)
                VALUES(?,?,?,'Draft')
            """,(
                month,rows[0],rows[1]
            ))

            log_action(
                "Create ECR draft",
                "ECR"
            )

            st.success("ECR draft created.")

    with tabs[1]:
        ecr_rows = execute("""
            SELECT id,month,members,amount,status
            FROM ecr
            ORDER BY id DESC
        """,fetch=True)

        for x in ecr_rows:

            st.write(
                f"**ECR #{x[0]}** | "
                f"{x[1]} | "
                f"Members: {x[2]} | "
                f"₹{x[3]:,.2f}"
            )

            if st.button(
                "Validate",
                key=f"validate{x[0]}"
            ):

                # Demo validation
                execute(
                    "UPDATE ecr SET status='Validated' WHERE id=?",
                    (x[0],)
                )

                log_action(
                    f"Validate ECR {x[0]}",
                    "ECR"
                )

                st.success("ECR validated.")
                st.rerun()

    with tabs[2]:

        ecr_rows = execute("""
            SELECT id,month,members,amount,status
            FROM ecr
            WHERE status='Validated'
        """,fetch=True)

        for x in ecr_rows:

            if st.button(
                f"Submit ECR #{x[0]}",
                key=f"submit{x[0]}"
            ):

                trrn = (
                    "DEMO"
                    + datetime.now().strftime("%Y%m%d")
                    + str(random.randint(10000,99999))
                )

                execute("""
                    UPDATE ecr
                    SET status='Submitted',trrn=?
                    WHERE id=?
                """,(trrn,x[0]))

                execute("""
                    INSERT INTO challans
                    (trrn,amount,status,created_at)
                    VALUES(?,?,?,?)
                """,(
                    trrn,
                    x[3],
                    "Unpaid",
                    datetime.now().isoformat()
                ))

                log_action(
                    f"Submit ECR {x[0]} / {trrn}",
                    "ECR"
                )

                st.success("ECR submitted — DEMO.")
                st.info(f"Demo TRRN: {trrn}")
                st.rerun()

    with tabs[3]:

        rows = execute("""
            SELECT id,month,members,amount,status,trrn
            FROM ecr
            ORDER BY id DESC
        """,fetch=True)

        st.dataframe(
            pd.DataFrame(
                rows,
                columns=[
                    "ID","Month","Members",
                    "Amount","Status","TRRN"
                ]
            ),
            use_container_width=True,
            hide_index=True
        )

    with tabs[4]:

        errors = execute("""
            SELECT id,ecr_id,employee_id,error,status
            FROM ecr_errors
            ORDER BY id DESC
        """,fetch=True)

        if errors:
            st.dataframe(
                pd.DataFrame(
                    errors,
                    columns=[
                        "ID","ECR","Employee",
                        "Error","Status"
                    ]
                ),
                use_container_width=True,
                hide_index=True
            )
        else:
            st.success("No ECR errors in demo.")


# =========================================================
# CHALLAN / PAYMENT
# =========================================================

def challan_payment():
    header("🧾 Challan / TRRN / Payment")

    tabs = st.tabs([
        "TRRN",
        "Challans",
        "Payment",
        "Reconciliation"
    ])

    with tabs[0]:
        rows = execute("""
            SELECT trrn,month,members,amount,status
            FROM ecr
            WHERE trrn IS NOT NULL
        """,fetch=True)

        st.dataframe(
            pd.DataFrame(
                rows,
                columns=[
                    "TRRN","Month","Members",
                    "Amount","ECR Status"
                ]
            ),
            use_container_width=True,
            hide_index=True
        )

    with tabs[1]:

        rows = execute("""
            SELECT id,trrn,amount,status,created_at
            FROM challans
            ORDER BY id DESC
        """,fetch=True)

        st.dataframe(
            pd.DataFrame(
                rows,
                columns=[
                    "ID","TRRN","Amount",
                    "Status","Created"
                ]
            ),
            use_container_width=True,
            hide_index=True
        )

    with tabs[2]:

        rows = execute("""
            SELECT id,trrn,amount,status
            FROM challans
            WHERE status='Unpaid'
        """,fetch=True)

        if not rows:
            st.success("No unpaid demo challans.")
        else:
            for x in rows:

                st.write(
                    f"TRRN: **{x[1]}** | "
                    f"Amount: **₹{x[2]:,.2f}**"
                )

                if st.button(
                    "Pay — DEMO",
                    key=f"pay{x[0]}"
                ):

                    ref = (
                        "DEMO-PAY-"
                        + str(random.randint(
                            100000,999999
                        ))
                    )

                    execute("""
                        INSERT INTO payments
                        (trrn,amount,payment_ref,status,created_at)
                        VALUES(?,?,?,?,?)
                    """,(
                        x[1],
                        x[2],
                        ref,
                        "Success",
                        datetime.now().isoformat()
                    ))

                    execute("""
                        UPDATE challans
                        SET status='Paid'
                        WHERE id=?
                    """,(x[0],))

                    log_action(
                        f"Demo payment {x[1]}",
                        "Payment"
                    )

                    st.success(
                        f"Demo payment successful. Reference: {ref}"
                    )

                    st.rerun()

    with tabs[3]:

        rows = execute("""
            SELECT trrn,amount,payment_ref,status,created_at
            FROM payments
            ORDER BY id DESC
        """,fetch=True)

        if rows:
            st.dataframe(
                pd.DataFrame(
                    rows,
                    columns=[
                        "TRRN","Amount",
                        "Payment Ref",
                        "Status","Date"
                    ]
                ),
                use_container_width=True,
                hide_index=True
            )
        else:
            st.info("No payments.")


# =========================================================
# EXIT
# =========================================================

def exit_module():
    header("🚪 Employee Exit")

    rows = execute("""
        SELECT id,name,uan,doj,status
        FROM employees
        WHERE status='Active'
    """,fetch=True)

    if not rows:
        st.info("No active employees.")
        return

    employee = st.selectbox(
        "Employee",
        [(x[0],x[1]) for x in rows],
        format_func=lambda x:x[1]
    )

    doe = st.date_input(
        "Date of Exit",
        date.today()
    )

    reason = st.selectbox(
        "Reason",
        [
            "Cessation of employment",
            "Retirement",
            "Resignation",
            "Other"
        ]
    )

    if st.button("Mark Exit — DEMO"):

        execute("""
            UPDATE employees
            SET doe=?,exit_reason=?,status='Exited'
            WHERE id=?
        """,(
            doe.isoformat(),
            reason,
            employee[0]
        ))

        log_action(
            f"Employee exit {employee[1]}",
            "Exit"
        )

        st.success("Employee marked as exited in demo.")
        st.rerun()


def exit_employee(employee_id):

    st.subheader("Employee Exit")

    if st.button(
        "Open Exit Workflow",
        key=f"exitopen{employee_id}"
    ):
        st.info(
            "Use the main Exit module for the complete demo workflow."
        )


# =========================================================
# CORRECTIONS
# =========================================================

def correction(employee_id=None):

    st.subheader("✏️ Correction Request")

    employees = execute(
        "SELECT id,name FROM employees",
        fetch=True
    )

    if not employees:
        return

    if employee_id:
        selected = employee_id
    else:
        selected = st.selectbox(
            "Employee",
            [(x[0],x[1]) for x in employees],
            format_func=lambda x:x[1]
        )[0]

    field = st.selectbox(
        "Correction Type",
        [
            "Name",
            "DOB",
            "Gender",
            "Father/Spouse Name",
            "DOJ",
            "DOE",
            "UAN",
            "Wage"
        ]
    )

    old = st.text_input("Old Value")
    new = st.text_input("New Value")
    reason = st.text_area("Reason")

    if st.button("Submit Correction"):

        execute("""
            INSERT INTO corrections
            (employee_id,field_name,old_value,
             new_value,reason,status,created_at)
            VALUES(?,?,?,?,?,'Pending',?)
        """,(
            selected,
            field,
            old,
            new,
            reason,
            datetime.now().isoformat()
        ))

        log_action(
            f"Correction request: {field}",
            "Corrections"
        )

        st.success("Correction request submitted — DEMO.")


# =========================================================
# APPROVALS
# =========================================================

def approvals():

    st.subheader("Pending Approvals")

    tabs = st.tabs([
        "KYC",
        "Corrections",
        "All"
    ])

    with tabs[0]:

        rows = execute("""
            SELECT k.id,e.name,e.uan,k.status
            FROM kyc k
            JOIN employees e ON e.id=k.employee_id
            WHERE k.status='Pending'
        """,fetch=True)

        for x in rows:

            st.write(
                f"{x[1]} | {x[2]} | {x[3]}"
            )

            c1,c2 = st.columns(2)

            if c1.button(
                "Approve",
                key=f"approve{x[0]}"
            ):
                execute(
                    "UPDATE kyc SET status='Approved' WHERE id=?",
                    (x[0],)
                )
                log_action(
                    "Approve KYC",
                    "Approvals"
                )
                st.rerun()

            if c2.button(
                "Reject",
                key=f"reject{x[0]}"
            ):
                execute(
                    "UPDATE kyc SET status='Rejected' WHERE id=?",
                    (x[0],)
                )
                log_action(
                    "Reject KYC",
                    "Approvals"
                )
                st.rerun()

    with tabs[1]:

        rows = execute("""
            SELECT id,employee_id,field_name,
                   old_value,new_value,reason,status
            FROM corrections
            WHERE status='Pending'
        """,fetch=True)

        for x in rows:

            st.write(
                f"Request #{x[0]} | "
                f"{x[2]} | "
                f"{x[3]} → {x[4]}"
            )

            if st.button(
                "Approve Correction",
                key=f"corr{x[0]}"
            ):

                execute("""
                    UPDATE corrections
                    SET status='Approved'
                    WHERE id=?
                """,(x[0],))

                log_action(
                    f"Approve correction {x[0]}",
                    "Approvals"
                )

                st.success(
                    "Correction approved — DEMO."
                )
                st.rerun()

    with tabs[2]:

        st.write("All pending demo approval workflows are shown in their respective tabs.")


# =========================================================
# COMPLIANCE
# =========================================================

def compliance():

    header("⚖️ Compliance / Notices")

    tabs = st.tabs([
        "Compliance",
        "Notices",
        "e-Proceedings — Demo"
    ])

    with tabs[0]:

        ecr_pending = execute("""
            SELECT COUNT(*)
            FROM ecr
            WHERE status!='Submitted'
        """,fetch=True)[0][0]

        unpaid = execute("""
            SELECT COUNT(*)
            FROM challans
            WHERE status='Unpaid'
        """,fetch=True)[0][0]

        kyc_pending = execute("""
            SELECT COUNT(*)
            FROM kyc
            WHERE status='Pending'
        """,fetch=True)[0][0]

        c1,c2,c3 = st.columns(3)

        c1.metric("ECR Pending",ecr_pending)
        c2.metric("Unpaid Challan",unpaid)
        c3.metric("KYC Pending",kyc_pending)

    with tabs[1]:

        rows = execute("""
            SELECT id,title,description,
                   due_date,status,response
            FROM notices
            ORDER BY id DESC
        """,fetch=True)

        if not rows:
            st.info("No notices in demo.")

        for x in rows:

            with st.expander(
                f"{x[1]} | {x[4]}"
            ):

                st.write(x[2])
                st.write("Due:",x[3])

                response = st.text_area(
                    "Employer Response",
                    key=f"response{x[0]}"
                )

                if st.button(
                    "Submit Response",
                    key=f"notice{x[0]}"
                ):

                    execute("""
                        UPDATE notices
                        SET response=?,status='Response Submitted'
                        WHERE id=?
                    """,(response,x[0]))

                    log_action(
                        "Notice response submitted",
                        "Compliance"
                    )

                    st.success("Response submitted — DEMO.")
                    st.rerun()

    with tabs[2]:

        st.info(
            "This is a simulated e-Proceedings training workflow."
        )

        st.selectbox(
            "Proceeding Status",
            [
                "Open",
                "Response Pending",
                "Response Submitted",
                "Under Review",
                "Closed"
            ]
        )


# =========================================================
# REPORTS
# =========================================================

def reports():

    header("📈 Reports")

    report = st.selectbox(
        "Report",
        [
            "Employee Report",
            "UAN Report",
            "KYC Report",
            "Payroll Report",
            "Contribution Report",
            "ECR Report",
            "Challan Report",
            "Payment Report",
            "Exit Report",
            "Correction Report",
            "Audit Report"
        ]
    )

    if report == "Employee Report":
        rows = execute("""
            SELECT member_id,uan,name,doj,doe,status
            FROM employees
        """,fetch=True)

        df = pd.DataFrame(
            rows,
            columns=[
                "Member ID","UAN","Name",
                "DOJ","DOE","Status"
            ]
        )

    elif report == "UAN Report":

        rows = execute("""
            SELECT name,uan,member_id,status
            FROM employees
        """,fetch=True)

        df = pd.DataFrame(
            rows,
            columns=[
                "Name","UAN",
                "Member ID","Status"
            ]
        )

    elif report == "KYC Report":

        rows = execute("""
            SELECT e.name,e.uan,
                   k.aadhaar,k.pan,
                   k.bank,k.status
            FROM kyc k
            JOIN employees e ON e.id=k.employee_id
        """,fetch=True)

        df = pd.DataFrame(
            rows,
            columns=[
                "Name","UAN","Aadhaar",
                "PAN","Bank","Status"
            ]
        )

    elif report == "Payroll Report":

        rows = execute("""
            SELECT e.name,p.month,p.basic,
                   p.employee_share,
                   p.employer_share
            FROM payroll p
            JOIN employees e ON e.id=p.employee_id
        """,fetch=True)

        df = pd.DataFrame(
            rows,
            columns=[
                "Name","Month","Basic",
                "Employee Share",
                "Employer Share"
            ]
        )

    elif report == "ECR Report":

        rows = execute("""
            SELECT id,month,members,
                   amount,status,trrn
            FROM ecr
        """,fetch=True)

        df = pd.DataFrame(
            rows,
            columns=[
                "ID","Month","Members",
                "Amount","Status","TRRN"
            ]
        )

    elif report == "Challan Report":

        rows = execute("""
            SELECT trrn,amount,
                   status,created_at
            FROM challans
        """,fetch=True)

        df = pd.DataFrame(
            rows,
            columns=[
                "TRRN","Amount",
                "Status","Created"
            ]
        )

    elif report == "Payment Report":

        rows = execute("""
            SELECT trrn,amount,
                   payment_ref,status,created_at
            FROM payments
        """,fetch=True)

        df = pd.DataFrame(
            rows,
            columns=[
                "TRRN","Amount",
                "Payment Ref",
                "Status","Created"
            ]
        )

    elif report == "Exit Report":

        rows = execute("""
            SELECT name,uan,doj,doe,
                   exit_reason,status
            FROM employees
            WHERE doe IS NOT NULL
        """,fetch=True)

        df = pd.DataFrame(
            rows,
            columns=[
                "Name","UAN","DOJ",
                "DOE","Reason","Status"
            ]
        )

    elif report == "Correction Report":

        rows = execute("""
            SELECT id,employee_id,
                   field_name,old_value,
                   new_value,status,created_at
            FROM corrections
        """,fetch=True)

        df = pd.DataFrame(
            rows,
            columns=[
                "ID","Employee","Field",
                "Old","New","Status","Created"
            ]
        )

    elif report == "Audit Report":

        rows = execute("""
            SELECT username,action,
                   module,created_at
            FROM audit_logs
            ORDER BY id DESC
        """,fetch=True)

        df = pd.DataFrame(
            rows,
            columns=[
                "User","Action",
                "Module","Created"
            ]
        )

    else:

        rows = execute("""
            SELECT e.name,p.month,
                   p.employee_share,
                   p.employer_share,
                   p.eps_share,
                   p.edli_share
            FROM payroll p
            JOIN employees e ON e.id=p.employee_id
        """,fetch=True)

        df = pd.DataFrame(
            rows,
            columns=[
                "Name","Month",
                "Employee Share",
                "Employer Share",
                "EPS","EDLI"
            ]
        )

    st.dataframe(
        df,
        use_container_width=True,
        hide_index=True
    )

    if not df.empty:

        csv = df.to_csv(index=False)

        st.download_button(
            "⬇️ Download CSV",
            csv,
            "demo_report.csv",
            "text/csv"
        )


# =========================================================
# DOWNLOADS
# =========================================================

def downloads():

    header("📥 Downloads")

    st.write("Generate demo files:")

    reports_list = [
        "Employee List",
        "UAN List",
        "KYC Report",
        "Payroll Report",
        "ECR Report",
        "Challan Report",
        "Payment Report"
    ]

    for r in reports_list:

        if st.button(
            f"Generate {r}",
            key=r
        ):

            rows = execute(
                "SELECT * FROM employees",
                fetch=True
            )

            df = pd.DataFrame(rows)

            st.download_button(
                f"Download {r}",
                df.to_csv(index=False),
                f"{r.lower().replace(' ','_')}.csv",
                "text/csv",
                key=f"download_{r}"
            )


# =========================================================
# NOTIFICATIONS
# =========================================================

def notifications():

    header("🔔 Notifications")

    rows = execute("""
        SELECT id,message,status,created_at
        FROM notifications
        ORDER BY id DESC
    """,fetch=True)

    if not rows:
        st.info("No notifications.")
        return

    for x in rows:

        if x[2] == "Unread":
            st.warning(x[1])
        else:
            st.info(x[1])

        if st.button(
            "Mark Read",
            key=f"read{x[0]}"
        ):

            execute(
                "UPDATE notifications SET status='Read' WHERE id=?",
                (x[0],)
            )

            st.rerun()


# =========================================================
# AUDIT
# =========================================================

def audit():

    header("📜 Audit Trail")

    rows = execute("""
        SELECT username,action,
               module,created_at
        FROM audit_logs
        ORDER BY id DESC
    """,fetch=True)

    st.dataframe(
        pd.DataFrame(
            rows,
            columns=[
                "User","Action",
                "Module","Date/Time"
            ]
        ),
        use_container_width=True,
        hide_index=True
    )


# =========================================================
# USER / ADMIN
# =========================================================

def user_admin():

    header("👤 User / Admin")

    tabs = st.tabs([
        "My Profile",
        "Users",
        "Roles",
        "Settings"
    ])

    with tabs[0]:

        st.write(
            "**Username:**",
            st.session_state.get(
                "username",
                "demoemployer"
            )
        )

        st.write(
            "**Role:**",
            st.session_state.get(
                "role",
                "Employer"
            )
        )

    with tabs[1]:

        rows = execute("""
            SELECT username,role,active
            FROM users
        """,fetch=True)

        st.dataframe(
            pd.DataFrame(
                rows,
                columns=[
                    "Username",
                    "Role",
                    "Active"
                ]
            ),
            use_container_width=True,
            hide_index=True
        )

    with tabs[2]:

        st.write("### Demo Roles")

        st.write("""
        - Employer
        - HR
        - Payroll Operator
        - Compliance Officer
        - Viewer
        - Administrator
        """)

    with tabs[3]:

        st.checkbox(
            "Demo notifications",
            value=True
        )

        st.checkbox(
            "Audit logging",
            value=True
        )


# =========================================================
# SPECIAL MODULES
# =========================================================

def special_modules():

    header("⭐ Special Modules")

    module = st.selectbox(
        "Select Module",
        [
            "ABRY — Demo",
            "Exemption — Demo",
            "Past Accumulation — Demo",
            "International Workers — Demo"
        ]
    )

    if module == "Past Accumulation — Demo":

        file = st.file_uploader(
            "Upload CSV",
            type=["csv"]
        )

        if file:
            df = pd.read_csv(file)

            st.dataframe(
                df,
                use_container_width=True
            )

            if st.button("Validate Upload"):
                st.success(
                    f"{len(df)} rows validated — DEMO."
                )

    else:

        st.info(
            f"{module} is available as a simulated training module."
        )

        if st.button("Create Demo Application"):
            st.success(
                "Demo application created."
            )


# =========================================================
# MAIN MENU
# =========================================================

def main():

    init_db()

    if not st.session_state.get("logged",False):
        login()
        return

    st.set_page_config(
        page_title="EPFO Employer Training Demo",
        page_icon="🏢",
        layout="wide",
        initial_sidebar_state="expanded"
    )

    st.sidebar.markdown(
        """
        # 🏢 EPFO Employer
        ### TRAINING DEMO
        """
    )

    st.sidebar.warning(
        "DEMO ONLY — Not official EPFO"
    )

    st.sidebar.divider()

    menu = st.sidebar.radio(
        "MAIN MENU",
        [
            "🏠 Dashboard",
            "🏢 Establishment",
            "👥 Member",
            "🪪 KYC",
            "💰 Payroll",
            "📄 ECR / Return Filing",
            "🧾 Challan / Payment",
            "🚪 Employee Exit",
            "✏️ Corrections",
            "⚖️ Compliance",
            "📈 Reports",
            "📥 Downloads",
            "🔔 Notifications",
            "📜 Audit Trail",
            "👤 User / Admin",
            "⭐ Special Modules"
        ]
    )

    st.sidebar.divider()

    if st.sidebar.button("🚪 Logout"):
        log_action("Logout","Authentication")
        st.session_state.clear()
        st.rerun()

    if menu == "🏠 Dashboard":
        dashboard()

    elif menu == "🏢 Establishment":
        establishment()

    elif menu == "👥 Member":
        members()

    elif menu == "🪪 KYC":
        kyc()

    elif menu == "💰 Payroll":
        payroll()

    elif menu == "📄 ECR / Return Filing":
        ecr()

    elif menu == "🧾 Challan / Payment":
        challan_payment()

    elif menu == "🚪 Employee Exit":
        exit_module()

    elif menu == "✏️ Corrections":
        correction()

    elif menu == "⚖️ Compliance":
        compliance()

    elif menu == "📈 Reports":
        reports()

    elif menu == "📥 Downloads":
        downloads()

    elif menu == "🔔 Notifications":
        notifications()

    elif menu == "📜 Audit Trail":
        audit()

    elif menu == "👤 User / Admin":
        user_admin()

    elif menu == "⭐ Special Modules":
        special_modules()


if __name__ == "__main__":
    main()
