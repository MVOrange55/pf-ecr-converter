import streamlit as st
import pandas as pd
import random
import string
from datetime import date, datetime
from pathlib import Path

# ============================================================
# EPFO EMPLOYER PORTAL — TRAINING DEMO
# ============================================================

st.set_page_config(
    page_title="EPFO Employer Portal — Training Demo",
    page_icon="🏢",
    layout="wide",
    initial_sidebar_state="expanded",
)

# -----------------------------
# Session state
# -----------------------------

def init_state():
    defaults = {
        "logged_in": False,
        "username": "",
        "company": {
            "name": "ABC Technologies Pvt. Ltd.",
            "code": "DLCPM0001234000",
            "pan": "ABCDE1234F",
            "address": "Cyber City, Gurugram, Haryana",
            "constitution": "Private Limited Company",
            "status": "Active",
            "mobile": "98XXXXXX10",
            "email": "demo@abctech.example",
        },
        "employees": [
            {
                "member_id": "DLCPM00012340000001",
                "name": "Rahul Sharma",
                "dob": "1995-04-12",
                "gender": "Male",
                "doj": "2024-04-01",
                "doe": "",
                "reason": "",
                "uan": "100000000001",
                "basic": 30000,
                "epf_wages": 15000,
                "eps_wages": 15000,
                "edli_wages": 15000,
                "aadhaar": "Verified",
                "pan": "Verified",
                "bank": "Verified",
                "kyc": "Approved",
                "status": "Active",
            },
            {
                "member_id": "DLCPM00012340000002",
                "name": "Priya Verma",
                "dob": "1997-09-21",
                "gender": "Female",
                "doj": "2024-06-10",
                "doe": "",
                "reason": "",
                "uan": "100000000002",
                "basic": 30000,
                "epf_wages": 15000,
                "eps_wages": 15000,
                "edli_wages": 15000,
                "aadhaar": "Pending",
                "pan": "Verified",
                "bank": "Pending",
                "kyc": "Pending",
                "status": "Active",
            },
        ],
        "ecr": [],
        "challans": [],
        "notices": [],
        "corrections": [],
        "logs": [],
    }

    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v


init_state()


# ============================================================
# Helpers
# ============================================================

def money(value):
    return f"₹{float(value):,.2f}"


def generate_uan():
    return "".join(random.choices(string.digits, k=12))


def generate_trrn():
    return "TRRN" + "".join(random.choices(string.digits, k=12))


def generate_member_id():
    company_code = st.session_state.company["code"]
    suffix = "".join(random.choices(string.digits, k=8))
    return f"{company_code}{suffix}"


def add_log(message):
    st.session_state.logs.insert(
        0,
        {
            "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "activity": message,
        },
    )


def calc_contribution(basic):
    """
    Demo calculation only.

    Employee EPF = 12% of EPF wages
    Employer EPF = 3.67%
    EPS = 8.33%
    EDLI = 0.5%

    This is a training calculation and should NOT be treated
    as official statutory calculation for actual filing.
    """
    epf_wages = min(float(basic), 15000)
    eps_wages = min(float(basic), 15000)
    edli_wages = min(float(basic), 15000)

    employee = round(epf_wages * 0.12, 2)
    eps = round(eps_wages * 0.0833, 2)
    employer_epf = round(eps_wages * 0.0367, 2)
    edli = round(edli_wages * 0.005, 2)

    employer_total = round(employer_epf + eps, 2)

    return {
        "epf_wages": epf_wages,
        "eps_wages": eps_wages,
        "edli_wages": edli_wages,
        "employee": employee,
        "employer_epf": employer_epf,
        "eps": eps,
        "edli": edli,
        "employer_total": employer_total,
        "total": round(employee + employer_total + edli, 2),
    }


def employee_dataframe():
    if not st.session_state.employees:
        return pd.DataFrame()

    rows = []

    for e in st.session_state.employees:
        c = calc_contribution(e["basic"])

        rows.append(
            {
                "Member ID": e["member_id"],
                "Name": e["name"],
                "UAN": e["uan"],
                "DOJ": e["doj"],
                "DOE": e["doe"],
                "Basic": e["basic"],
                "EPF Wages": c["epf_wages"],
                "Employee PF": c["employee"],
                "Employer PF": c["employer_total"],
                "KYC": e["kyc"],
                "Status": e["status"],
            }
        )

    return pd.DataFrame(rows)


def csv_download(df):
    return df.to_csv(index=False).encode("utf-8")


# ============================================================
# Login
# ============================================================

if not st.session_state.logged_in:

    st.markdown(
        """
        <div style="
            background:linear-gradient(90deg,#064e3b,#047857);
            padding:25px;
            border-radius:12px;
            color:white;
            text-align:center;
        ">
            <h1>🏢 EPFO Employer Portal</h1>
            <p style="font-size:18px;">
                Training / Simulation Environment
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.warning(
        "DEMO ONLY — This application is not connected to EPFO. "
        "Do not enter real EPFO passwords, OTPs, Aadhaar, PAN or bank details."
    )

    st.markdown("### Employer Login")

    col1, col2, col3 = st.columns([1, 2, 1])

    with col2:
        username = st.text_input(
            "Employer User ID",
            value="DEMOEMP001",
        )

        password = st.text_input(
            "Password",
            type="password",
            value="demo123",
        )

        captcha = st.text_input(
            "Captcha",
            value="DEMO",
        )

        st.caption("Demo credentials: DEMOEMP001 / demo123 / DEMO")

        if st.button(
            "🔐 Login",
            type="primary",
            use_container_width=True,
        ):
            if username == "DEMOEMP001" and password == "demo123":
                st.session_state.logged_in = True
                st.session_state.username = username
                add_log("Employer logged in")
                st.rerun()
            else:
                st.error("Invalid demo credentials.")

        c1, c2 = st.columns(2)

        with c1:
            if st.button("Forgot Password"):
                st.info("Demo: Password reset workflow opened.")

        with c2:
            if st.button("Account Unlock"):
                st.info("Demo: Account unlock request created.")

    st.stop()


# ============================================================
# Sidebar
# ============================================================

company = st.session_state.company

st.sidebar.markdown(
    """
    <div style="
        background:#064e3b;
        color:white;
        padding:15px;
        border-radius:10px;
        text-align:center;
    ">
        <h3>EPFO Employer</h3>
        <small>Training Demo</small>
    </div>
    """,
    unsafe_allow_html=True,
)

st.sidebar.write(f"**Establishment:** {company['code']}")
st.sidebar.write(f"**Employer:** {st.session_state.username}")

menu = st.sidebar.radio(
    "MENU",
    [
        "🏠 Dashboard",
        "1️⃣ Establishment Registration",
        "2️⃣ Employer Login",
        "3️⃣ Establishment / Profile",
        "4️⃣ Employee / Member",
        "5️⃣ KYC",
        "6️⃣ UAN Management",
        "7️⃣ Salary / Contribution",
        "8️⃣ ECR Filing",
        "9️⃣ ECR Errors",
        "🔟 Challan / TRRN",
        "1️⃣1️⃣ Payment Reconciliation",
        "1️⃣2️⃣ Employee Exit",
        "1️⃣3️⃣ Transfer / Previous Employment",
        "1️⃣4️⃣ Online Services",
        "1️⃣5️⃣ Compliance Dashboard",
        "1️⃣6️⃣ Downloads",
        "1️⃣7️⃣ Reports",
        "1️⃣8️⃣ Corrections",
        "1️⃣9️⃣ Notices / e-Proceedings",
        "2️⃣0️⃣ Special Modules",
        "⚙️ Settings / Reset",
    ],
)

if st.sidebar.button("🚪 Logout", use_container_width=True):
    st.session_state.logged_in = False
    st.session_state.username = ""
    st.rerun()


# ============================================================
# Header
# ============================================================

st.title("EPFO Employer Portal")
st.caption(
    "Training & Simulation Demo • Dummy Data • Not connected to EPFO"
)

st.divider()


# ============================================================
# 0. Dashboard
# ============================================================

if menu == "🏠 Dashboard":

    st.subheader("Employer Dashboard")

    active = len(
        [e for e in st.session_state.employees if e["status"] == "Active"]
    )

    pending_kyc = len(
        [e for e in st.session_state.employees if e["kyc"] == "Pending"]
    )

    pending_ecr = len(
        [x for x in st.session_state.ecr if x["status"] != "Paid"]
    )

    paid_challans = len(
        [x for x in st.session_state.challans if x["status"] == "Paid"]
    )

    c1, c2, c3, c4 = st.columns(4)

    c1.metric("Active Employees", active)
    c2.metric("Pending KYC", pending_kyc)
    c3.metric("Pending ECR", pending_ecr)
    c4.metric("Paid Challans", paid_challans)

    st.subheader("Alerts and To Do Tasks")

    alerts = []

    if pending_kyc:
        alerts.append(f"⚠️ {pending_kyc} employee KYC item(s) pending.")

    if not st.session_state.ecr:
        alerts.append("📄 Monthly ECR has not been created in this demo.")

    if not alerts:
        alerts.append("✅ No pending demo tasks.")

    for alert in alerts:
        st.info(alert)

    st.subheader("Recent Activity")

    if st.session_state.logs:
        st.dataframe(
            pd.DataFrame(st.session_state.logs[:10]),
            use_container_width=True,
            hide_index=True,
        )
    else:
        st.info("No activity yet.")


# ============================================================
# 1. Establishment Registration
# ============================================================

elif menu == "1️⃣ Establishment Registration":

    st.subheader("Establishment Registration — Demo")

    st.info(
        "This is a simulated registration form. It does not submit "
        "anything to EPFO."
    )

    with st.form("registration"):

        name = st.text_input(
            "Establishment Name",
            company["name"],
        )

        constitution = st.selectbox(
            "Constitution",
            [
                "Private Limited Company",
                "Public Limited Company",
                "Partnership",
                "LLP",
                "Proprietorship",
                "Trust",
                "Society",
            ],
        )

        pan = st.text_input("PAN", company["pan"])

        address = st.text_area(
            "Registered Address",
            company["address"],
        )

        state = st.selectbox(
            "State",
            [
                "Haryana",
                "Delhi",
                "Maharashtra",
                "Karnataka",
                "Tamil Nadu",
                "Uttar Pradesh",
                "Other",
            ],
        )

        authorized = st.text_input(
            "Authorized Signatory",
            "Demo Authorized Person",
        )

        mobile = st.text_input(
            "Mobile",
            company["mobile"],
        )

        email = st.text_input(
            "Email",
            company["email"],
        )

        submitted = st.form_submit_button(
            "Submit Registration — DEMO",
            type="primary",
        )

        if submitted:

            company.update(
                {
                    "name": name,
                    "constitution": constitution,
                    "pan": pan,
                    "address": address,
                    "mobile": mobile,
                    "email": email,
                }
            )

            add_log("Demo establishment registration submitted")

            st.success(
                "Demo registration submitted successfully."
            )

            st.code(
                f"""
Application Number : DEMO-REG-2026-001
Establishment Code : {company['code']}
Status             : Demo Submitted
State              : {state}
                """
            )


# ============================================================
# 2. Employer Login
# ============================================================

elif menu == "2️⃣ Employer Login":

    st.subheader("Employer Login Information")

    st.success("You are currently logged in.")

    st.write("**Demo User ID:**", st.session_state.username)
    st.write("**Establishment Code:**", company["code"])

    st.info(
        "Actual EPFO password/OTP functionality is intentionally "
        "not implemented in this training clone."
    )

    if st.button("Simulate Password Change"):
        add_log("Demo password-change workflow opened")
        st.success("Demo password changed successfully.")


# ============================================================
# 3. Establishment Profile
# ============================================================

elif menu == "3️⃣ Establishment / Profile":

    st.subheader("Establishment Profile")

    with st.form("profile"):

        company["name"] = st.text_input(
            "Establishment Name",
            company["name"],
        )

        company["pan"] = st.text_input(
            "PAN",
            company["pan"],
        )

        company["address"] = st.text_area(
            "Address",
            company["address"],
        )

        company["constitution"] = st.selectbox(
            "Constitution",
            [
                "Private Limited Company",
                "Public Limited Company",
                "Partnership",
                "LLP",
                "Proprietorship",
            ],
            index=0,
        )

        company["mobile"] = st.text_input(
            "Mobile",
            company["mobile"],
        )

        company["email"] = st.text_input(
            "Email",
            company["email"],
        )

        if st.form_submit_button(
            "Save Profile",
            type="primary",
        ):
            add_log("Establishment profile updated")
            st.success("Profile saved in demo session.")

    st.divider()

    st.write("### Establishment Status")

    c1, c2, c3 = st.columns(3)

    c1.metric("Establishment Code", company["code"])
    c2.metric("Status", company["status"])
    c3.metric("Constitution", company["constitution"])


# ============================================================
# 4. Employee / Member
# ============================================================

elif menu == "4️⃣ Employee / Member":

    st.subheader("Employee / Member Management")

    tab1, tab2 = st.tabs(
        [
            "➕ Add Employee",
            "📋 Employee List",
        ]
    )

    with tab1:

        with st.form("add_employee"):

            name = st.text_input("Employee Name")

            dob = st.date_input(
                "Date of Birth",
                date(1995, 1, 1),
            )

            gender = st.selectbox(
                "Gender",
                ["Male", "Female", "Other"],
            )

            doj = st.date_input(
                "Date of Joining",
                date.today(),
            )

            basic = st.number_input(
                "Basic Wages",
                min_value=0.0,
                value=30000.0,
                step=500.0,
            )

            existing = st.radio(
                "Previous UAN?",
                [
                    "Yes — Existing UAN",
                    "No — Generate Demo UAN",
                ],
            )

            old_uan = ""

            if existing.startswith("Yes"):
                old_uan = st.text_input(
                    "Existing UAN",
                    "100000000099",
                )

            aadhaar = st.selectbox(
                "Aadhaar KYC",
                ["Pending", "Verified", "Rejected"],
            )

            pan_status = st.selectbox(
                "PAN KYC",
                ["Pending", "Verified", "Rejected"],
            )

            bank = st.selectbox(
                "Bank KYC",
                ["Pending", "Verified", "Rejected"],
            )

            save = st.form_submit_button(
                "Add Employee",
                type="primary",
            )

            if save:

                uan = (
                    old_uan
                    if existing.startswith("Yes")
                    else generate_uan()
                )

                kyc = (
                    "Approved"
                    if (
                        aadhaar == "Verified"
                        and pan_status == "Verified"
                        and bank == "Verified"
                    )
                    else "Pending"
                )

                emp = {
                    "member_id": generate_member_id(),
                    "name": name or "Demo Employee",
                    "dob": str(dob),
                    "gender": gender,
                    "doj": str(doj),
                    "doe": "",
                    "reason": "",
                    "uan": uan,
                    "basic": basic,
                    "epf_wages": min(basic, 15000),
                    "eps_wages": min(basic, 15000),
                    "edli_wages": min(basic, 15000),
                    "aadhaar": aadhaar,
                    "pan": pan_status,
                    "bank": bank,
                    "kyc": kyc,
                    "status": "Active",
                }

                st.session_state.employees.append(emp)

                add_log(
                    f"Employee added: {emp['name']} / UAN {uan}"
                )

                st.success(
                    f"Employee added. Demo UAN: {uan}"
                )

    with tab2:

        df = employee_dataframe()

        if not df.empty:
            st.dataframe(
                df,
                use_container_width=True,
                hide_index=True,
            )
        else:
            st.info("No employees.")


# ============================================================
# 5. KYC
# ============================================================

elif menu == "5️⃣ KYC":

    st.subheader("KYC Management")

    if not st.session_state.employees:
        st.info("No employees available.")
    else:

        options = {
            f"{e['name']} — {e['uan']}": i
            for i, e in enumerate(st.session_state.employees)
        }

        selected = st.selectbox(
            "Select Employee",
            list(options.keys()),
        )

        idx = options[selected]
        emp = st.session_state.employees[idx]

        st.write(f"### {emp['name']}")

        c1, c2, c3 = st.columns(3)

        c1.metric("Aadhaar", emp["aadhaar"])
        c2.metric("PAN", emp["pan"])
        c3.metric("Bank", emp["bank"])

        col1, col2, col3 = st.columns(3)

        with col1:
            if st.button("Verify Aadhaar"):
                emp["aadhaar"] = "Verified"
                add_log(f"Aadhaar verified: {emp['name']}")
                st.rerun()

        with col2:
            if st.button("Verify PAN"):
                emp["pan"] = "Verified"
                add_log(f"PAN verified: {emp['name']}")
                st.rerun()

        with col3:
            if st.button("Verify Bank"):
                emp["bank"] = "Verified"
                add_log(f"Bank KYC verified: {emp['name']}")
                st.rerun()

        if (
            emp["aadhaar"] == "Verified"
            and emp["pan"] == "Verified"
            and emp["bank"] == "Verified"
        ):
            emp["kyc"] = "Approved"

        st.success(f"KYC Status: {emp['kyc']}")

        if st.button("Reject Demo KYC"):
            emp["kyc"] = "Rejected"
            add_log(f"KYC rejected: {emp['name']}")
            st.rerun()


# ============================================================
# 6. UAN
# ============================================================

elif menu == "6️⃣ UAN Management":

    st.subheader("UAN Management")

    df = employee_dataframe()

    if not df.empty:
        st.dataframe(
            df[["Name", "UAN", "Member ID", "Status"]],
            use_container_width=True,
            hide_index=True,
        )

    st.divider()

    st.write("### Generate Demo UAN")

    if st.button("Generate New Demo UAN"):

        uan = generate_uan()

        st.success(
            f"Generated Demo UAN: {uan}"
        )

        add_log(f"Demo UAN generated: {uan}")

    st.write("### UAN Linking")

    uan_input = st.text_input(
        "Enter Demo UAN"
    )

    if st.button("Check UAN"):

        found = any(
            e["uan"] == uan_input
            for e in st.session_state.employees
        )

        if found:
            st.success("UAN found in demo database.")
        else:
            st.warning("UAN not found in demo database.")


# ============================================================
# 7. Salary / Contribution
# ============================================================

elif menu == "7️⃣ Salary / Contribution":

    st.subheader("Salary & EPF Contribution Calculator")

    basic = st.number_input(
        "Basic Wages",
        min_value=0.0,
        value=30000.0,
        step=500.0,
    )

    c = calc_contribution(basic)

    cols = st.columns(4)

    cols[0].metric(
        "EPF Wages",
        money(c["epf_wages"]),
    )

    cols[1].metric(
        "Employee PF",
        money(c["employee"]),
    )

    cols[2].metric(
        "Employer PF",
        money(c["employer_total"]),
    )

    cols[3].metric(
        "EDLI",
        money(c["edli"]),
    )

    st.write("### Calculation Breakdown")

    calc_df = pd.DataFrame(
        [
            ["Employee EPF", c["employee"]],
            ["Employer EPF", c["employer_epf"]],
            ["EPS", c["eps"]],
            ["EDLI", c["edli"]],
            ["Total Demo Contribution", c["total"]],
        ],
        columns=["Component", "Amount"],
    )

    st.dataframe(
        calc_df,
        use_container_width=True,
        hide_index=True,
    )

    st.warning(
        "These percentages/limits are simplified for demonstration. "
        "Do not use this calculator for an actual statutory filing."
    )


# ============================================================
# 8. ECR
# ============================================================

elif menu == "8️⃣ ECR Filing":

    st.subheader("Monthly ECR — Demo")

    month = st.selectbox(
        "Contribution Month",
        [
            "April 2026",
            "May 2026",
            "June 2026",
            "July 2026",
            "August 2026",
            "September 2026",
        ],
    )

    active_employees = [
        e
        for e in st.session_state.employees
        if e["status"] == "Active"
    ]

    if not active_employees:
        st.warning("No active employees.")
    else:

        rows = []

        for e in active_employees:

            c = calc_contribution(e["basic"])

            rows.append(
                {
                    "UAN": e["uan"],
                    "Name": e["name"],
                    "EPF Wages": c["epf_wages"],
                    "EPS Wages": c["eps_wages"],
                    "EDLI Wages": c["edli_wages"],
                    "Employee Share": c["employee"],
                    "Employer EPF": c["employer_epf"],
                    "EPS": c["eps"],
                    "EDLI": c["edli"],
                }
            )

        ecr_df = pd.DataFrame(rows)

        st.dataframe(
            ecr_df,
            use_container_width=True,
            hide_index=True,
        )

        total_employee = ecr_df["Employee Share"].sum()
        total_employer = (
            ecr_df["Employer EPF"].sum()
            + ecr_df["EPS"].sum()
        )

        total = (
            total_employee
            + total_employer
            + ecr_df["EDLI"].sum()
        )

        c1, c2, c3 = st.columns(3)

        c1.metric(
            "Employee Share",
            money(total_employee),
        )

        c2.metric(
            "Employer Share",
            money(total_employer),
        )

        c3.metric(
            "Total Demo",
            money(total),
        )

        if st.button(
            "1. Validate ECR",
            type="secondary",
        ):

            errors = []

            for e in active_employees:

                if len(e["uan"]) != 12:
                    errors.append(
                        f"{e['name']}: Invalid UAN"
                    )

                if e["basic"] <= 0:
                    errors.append(
                        f"{e['name']}: Invalid wages"
                    )

            if errors:
                st.error("ECR validation failed.")

                for error in errors:
                    st.write("❌", error)

            else:
                st.success(
                    "ECR validation successful."
                )

                st.session_state["validated_ecr"] = {
                    "month": month,
                    "df": ecr_df,
                    "total": total,
                }

        if st.button(
            "2. Submit ECR",
            type="primary",
        ):

            if "validated_ecr" not in st.session_state:
                st.error(
                    "Validate ECR before submission."
                )
            else:

                trrn = generate_trrn()

                record = {
                    "month": month,
                    "trrn": trrn,
                    "employees": len(active_employees),
                    "amount": total,
                    "status": "Submitted",
                    "created": datetime.now().strftime(
                        "%Y-%m-%d %H:%M:%S"
                    ),
                }

                st.session_state.ecr.append(record)

                add_log(
                    f"ECR submitted for {month}, TRRN {trrn}"
                )

                st.success(
                    "ECR submitted successfully in demo."
                )

                st.code(
                    f"""
Month : {month}
TRRN  : {trrn}
Amount: {money(total)}
Status: Submitted
                    """
                )


# ============================================================
# 9. ECR Errors
# ============================================================

elif menu == "9️⃣ ECR Errors":

    st.subheader("ECR Error Simulator")

    error_type = st.selectbox(
        "Select Error",
        [
            "Invalid UAN",
            "Duplicate UAN",
            "Wrong Wages",
            "Invalid Member",
            "DOJ Problem",
            "DOE Problem",
            "Missing KYC",
            "Previous Employment Issue",
        ],
    )

    if st.button("Simulate Error"):

        solutions = {
            "Invalid UAN":
                "Verify the UAN format and employee record.",
            "Duplicate UAN":
                "Check whether the same UAN is already mapped.",
            "Wrong Wages":
                "Review payroll and ECR wage values.",
            "Invalid Member":
                "Verify Member ID and UAN mapping.",
            "DOJ Problem":
                "Check date of joining.",
            "DOE Problem":
                "Verify exit date and reason.",
            "Missing KYC":
                "Complete required KYC verification.",
            "Previous Employment Issue":
                "Verify previous employment/UAN history.",
        }

        st.error(error_type)
        st.info(solutions[error_type])


# ============================================================
# 10. Challan / TRRN
# ============================================================

elif menu == "🔟 Challan / TRRN":

    st.subheader("Challan / TRRN Management")

    if not st.session_state.ecr:

        st.info(
            "Submit an ECR first to create a demo challan."
        )

    else:

        for ecr in st.session_state.ecr:

            st.write(
                f"### {ecr['month']} — {ecr['trrn']}"
            )

            st.write(
                f"Amount: **{money(ecr['amount'])}**"
            )

            existing = next(
                (
                    c
                    for c in st.session_state.challans
                    if c["trrn"] == ecr["trrn"]
                ),
                None,
            )

            if not existing:

                if st.button(
                    f"Generate Challan — {ecr['trrn']}",
                    key=f"challan_{ecr['trrn']}",
                ):

                    challan = {
                        "trrn": ecr["trrn"],
                        "challan_no":
                            "CHL" +
                            "".join(
                                random.choices(
                                    string.digits,
                                    k=10,
                                )
                            ),
                        "amount": ecr["amount"],
                        "status": "Unpaid",
                        "date":
                            date.today().isoformat(),
                    }

                    st.session_state.challans.append(
                        challan
                    )

                    add_log(
                        f"Challan generated: {challan['challan_no']}"
                    )

                    st.rerun()

            else:

                st.success(
                    f"Challan: {existing['challan_no']}"
                )

                st.write(
                    f"Status: **{existing['status']}**"
                )

                if existing["status"] == "Unpaid":

                    if st.button(
                        "Pay Challan — DEMO",
                        key=f"pay_{existing['trrn']}",
                        type="primary",
                    ):

                        existing["status"] = "Paid"

                        add_log(
                            f"Demo challan paid: "
                            f"{existing['challan_no']}"
                        )

                        st.success(
                            "Demo payment successful."
                        )

                        st.rerun()


# ============================================================
# 11. Payment Reconciliation
# ============================================================

elif menu == "1️⃣1️⃣ Payment Reconciliation":

    st.subheader("Payment Reconciliation")

    if st.session_state.challans:

        df = pd.DataFrame(
            st.session_state.challans
        )

        st.dataframe(
            df,
            use_container_width=True,
            hide_index=True,
        )

        paid = len(
            [
                x
                for x in st.session_state.challans
                if x["status"] == "Paid"
            ]
        )

        unpaid = len(
            [
                x
                for x in st.session_state.challans
                if x["status"] != "Paid"
            ]
        )

        c1, c2 = st.columns(2)

        c1.metric("Paid", paid)
        c2.metric("Pending", unpaid)

    else:
        st.info("No challans available.")


# ============================================================
# 12. Employee Exit
# ============================================================

elif menu == "1️⃣2️⃣ Employee Exit":

    st.subheader("Employee Exit")

    active = [
        (i, e)
        for i, e in enumerate(
            st.session_state.employees
        )
        if e["status"] == "Active"
    ]

    if not active:

        st.info("No active employees.")

    else:

        choices = {
            f"{e['name']} — {e['uan']}": i
            for i, e in active
        }

        selected = st.selectbox(
            "Employee",
            list(choices.keys()),
        )

        idx = choices[selected]

        emp = st.session_state.employees[idx]

        exit_date = st.date_input(
            "Date of Exit",
            date.today(),
        )

        reason = st.selectbox(
            "Reason",
            [
                "Cessation of employment",
                "Superannuation",
                "Death",
                "Permanent disablement",
                "Other",
            ],
        )

        if st.button(
            "Mark Exit — DEMO",
            type="primary",
        ):

            emp["doe"] = str(exit_date)
            emp["reason"] = reason
            emp["status"] = "Exited"

            add_log(
                f"Employee exit marked: {emp['name']}"
            )

            st.success(
                f"{emp['name']} marked as exited."
            )


# ============================================================
# 13. Transfer / Previous Employment
# ============================================================

elif menu == "1️⃣3️⃣ Transfer / Previous Employment":

    st.subheader(
        "Transfer / Previous Employment — Demo"
    )

    uan = st.text_input(
        "UAN",
        "100000000001",
    )

    previous_member = st.text_input(
        "Previous Member ID",
        "DLCPM000000000001",
    )

    current_member = st.text_input(
        "Current Member ID",
        company["code"] + "00000003",
    )

    if st.button("Check Employment History"):

        found = next(
            (
                e
                for e in st.session_state.employees
                if e["uan"] == uan
            ),
            None,
        )

        if found:

            st.success(
                f"Employee found: {found['name']}"
            )

            st.write(
                f"Previous Member ID: {previous_member}"
            )

            st.write(
                f"Current Member ID: {current_member}"
            )

        else:
            st.warning(
                "UAN not found in demo database."
            )

    if st.button("Simulate Transfer Request"):

        add_log(
            f"Demo transfer request created for UAN {uan}"
        )

        st.success(
            "Demo transfer request created."
        )


# ============================================================
# 14. Online Services
# ============================================================

elif menu == "1️⃣4️⃣ Online Services":

    st.subheader("Online Services")

    services = [
        "Employer Profile",
        "Member Management",
        "KYC Management",
        "UAN Services",
        "ECR Filing",
        "Challan",
        "Payment Status",
        "Member Exit",
        "Transfer / Employment History",
        "Correction Request",
        "Compliance Services",
        "Reports",
    ]

    for service in services:

        if st.button(
            service,
            use_container_width=True,
        ):

            add_log(
                f"Opened demo service: {service}"
            )

            st.success(
                f"{service} demo opened."
            )


# ============================================================
# 15. Compliance Dashboard
# ============================================================

elif menu == "1️⃣5️⃣ Compliance Dashboard":

    st.subheader("Compliance Dashboard")

    total_employees = len(
        st.session_state.employees
    )

    active_employees = len(
        [
            e
            for e in st.session_state.employees
            if e["status"] == "Active"
        ]
    )

    kyc_pending = len(
        [
            e
            for e in st.session_state.employees
            if e["kyc"] == "Pending"
        ]
    )

    c1, c2, c3 = st.columns(3)

    c1.metric(
        "Total Members",
        total_employees,
    )

    c2.metric(
        "Active Members",
        active_employees,
    )

    c3.metric(
        "KYC Pending",
        kyc_pending,
    )

    st.write("### Compliance Checklist")

    checks = [
        ("Establishment Active", company["status"] == "Active"),
        ("Employees Added", total_employees > 0),
        ("KYC Review", kyc_pending == 0),
        ("ECR Created", len(st.session_state.ecr) > 0),
        ("Challan Generated", len(st.session_state.challans) > 0),
    ]

    for name, result in checks:

        if result:
            st.success(f"✅ {name}")
        else:
            st.warning(f"⚠️ {name}")


# ============================================================
# 16. Downloads
# ============================================================

elif menu == "1️⃣6️⃣ Downloads":

    st.subheader("Downloads")

    df = employee_dataframe()

    if not df.empty:

        st.download_button(
            "⬇️ Download Employee Report",
            data=csv_download(df),
            file_name="employee_report_demo.csv",
            mime="text/csv",
        )

    if st.session_state.ecr:

        ecr_df = pd.DataFrame(
            st.session_state.ecr
        )

        st.download_button(
            "⬇️ Download ECR Summary",
            data=csv_download(ecr_df),
            file_name="ecr_summary_demo.csv",
            mime="text/csv",
        )

    if st.session_state.challans:

        challan_df = pd.DataFrame(
            st.session_state.challans
        )

        st.download_button(
            "⬇️ Download Challan Report",
            data=csv_download(challan_df),
            file_name="challan_report_demo.csv",
            mime="text/csv",
        )

    if st.session_state.logs:

        logs_df = pd.DataFrame(
            st.session_state.logs
        )

        st.download_button(
            "⬇️ Download Activity Log",
            data=csv_download(logs_df),
            file_name="activity_log_demo.csv",
            mime="text/csv",
        )


# ============================================================
# 17. Reports
# ============================================================

elif menu == "1️⃣7️⃣ Reports":

    st.subheader("Reports")

    report_type = st.selectbox(
        "Report",
        [
            "Member-wise Report",
            "Monthly Contribution",
            "Challan / TRRN",
            "Payment Reconciliation",
            "UAN Report",
            "Establishment Report",
        ],
    )

    if report_type == "Member-wise Report":

        df = employee_dataframe()

        st.dataframe(
            df,
            use_container_width=True,
            hide_index=True,
        )

    elif report_type == "Monthly Contribution":

        rows = []

        for e in st.session_state.employees:

            c = calc_contribution(e["basic"])

            rows.append(
                {
                    "Employee": e["name"],
                    "UAN": e["uan"],
                    "Employee Share": c["employee"],
                    "Employer EPF": c["employer_epf"],
                    "EPS": c["eps"],
                    "EDLI": c["edli"],
                }
            )

        st.dataframe(
            pd.DataFrame(rows),
            use_container_width=True,
            hide_index=True,
        )

    elif report_type == "Challan / TRRN":

        if st.session_state.challans:
            st.dataframe(
                pd.DataFrame(
                    st.session_state.challans
                ),
                use_container_width=True,
                hide_index=True,
            )
        else:
            st.info("No challans.")

    elif report_type == "Payment Reconciliation":

        if st.session_state.challans:

            rows = []

            for c in st.session_state.challans:

                rows.append(
                    {
                        "TRRN": c["trrn"],
                        "Challan": c["challan_no"],
                        "Amount": c["amount"],
                        "Status": c["status"],
                    }
                )

            st.dataframe(
                pd.DataFrame(rows),
                use_container_width=True,
                hide_index=True,
            )

        else:
            st.info("No payment records.")

    elif report_type == "UAN Report":

        rows = [
            {
                "Name": e["name"],
                "UAN": e["uan"],
                "Member ID": e["member_id"],
                "Status": e["status"],
            }
            for e in st.session_state.employees
        ]

        st.dataframe(
            pd.DataFrame(rows),
            use_container_width=True,
            hide_index=True,
        )

    else:

        st.json(
            {
                "Establishment": company,
                "Employee Count":
                    len(st.session_state.employees),
                "ECR Count":
                    len(st.session_state.ecr),
                "Challan Count":
                    len(st.session_state.challans),
            }
        )


# ============================================================
# 18. Corrections
# ============================================================

elif menu == "1️⃣8️⃣ Corrections":

    st.subheader("Correction Request — Demo")

    employees = st.session_state.employees

    if employees:

        choices = {
            f"{e['name']} — {e['uan']}": i
            for i, e in enumerate(employees)
        }

        selected = st.selectbox(
            "Employee",
            list(choices.keys()),
        )

        idx = choices[selected]

        correction_type = st.selectbox(
            "Correction Type",
            [
                "Employee Name",
                "Date of Birth",
                "Father / Spouse Name",
                "Aadhaar / KYC",
                "UAN",
                "Date of Joining",
                "Date of Exit",
                "Wages / Contribution",
                "Employer Profile",
            ],
        )

        old_value = st.text_input(
            "Existing Value"
        )

        new_value = st.text_input(
            "Requested Value"
        )

        reason = st.text_area(
            "Reason for Correction"
        )

        if st.button(
            "Submit Correction Request",
            type="primary",
        ):

            request_id = (
                "CORR-"
                + "".join(
                    random.choices(
                        string.digits,
                        k=8,
                    )
                )
            )

            st.session_state.corrections.append(
                {
                    "request_id": request_id,
                    "employee": employees[idx]["name"],
                    "type": correction_type,
                    "old": old_value,
                    "new": new_value,
                    "reason": reason,
                    "status": "Pending Approval",
                    "date": datetime.now().strftime(
                        "%Y-%m-%d"
                    ),
                }
            )

            add_log(
                f"Correction request created: {request_id}"
            )

            st.success(
                f"Correction request created: {request_id}"
            )

    if st.session_state.corrections:

        st.write("### Correction Requests")

        st.dataframe(
            pd.DataFrame(
                st.session_state.corrections
            ),
            use_container_width=True,
            hide_index=True,
        )


# ============================================================
# 19. Notices / e-Proceedings
# ============================================================

elif menu == "1️⃣9️⃣ Notices / e-Proceedings":

    st.subheader("Compliance Notices / e-Proceedings")

    st.info(
        "This is a simulated compliance module."
    )

    with st.form("notice"):

        notice_type = st.selectbox(
            "Notice Type",
            [
                "Contribution Default",
                "Return Pending",
                "KYC Issue",
                "Wage Discrepancy",
                "General Compliance",
            ],
        )

        subject = st.text_input(
            "Subject",
            "Demo compliance notice",
        )

        details = st.text_area(
            "Details",
            "This is a simulated notice.",
        )

        if st.form_submit_button(
            "Create Demo Notice"
        ):

            notice_id = (
                "NOTICE-"
                + "".join(
                    random.choices(
                        string.digits,
                        k=8,
                    )
                )
            )

            st.session_state.notices.append(
                {
                    "notice_id": notice_id,
                    "type": notice_type,
                    "subject": subject,
                    "details": details,
                    "status": "Open",
                    "date": date.today().isoformat(),
                }
            )

            add_log(
                f"Compliance notice created: {notice_id}"
            )

            st.success(
                f"Notice {notice_id} created."
            )

    if st.session_state.notices:

        st.write("### Notices")

        st.dataframe(
            pd.DataFrame(
                st.session_state.notices
            ),
            use_container_width=True,
            hide_index=True,
        )

        notice_options = {
            n["notice_id"]: n
            for n in st.session_state.notices
        }

        selected_notice = st.selectbox(
            "Select Notice",
            list(notice_options.keys()),
        )

        if st.button("Submit Demo Response"):

            notice_options[selected_notice][
                "status"
            ] = "Response Submitted"

            add_log(
                f"Response submitted: {selected_notice}"
            )

            st.success(
                "Demo response submitted."
            )


# ============================================================
# 20. Special Modules
# ============================================================

elif menu == "2️⃣0️⃣ Special Modules":

    st.subheader("Special Modules")

    module = st.selectbox(
        "Module",
        [
            "ABRY — Demo",
            "Exemption — Demo",
            "Past Accumulation File Upload — Demo",
            "International Worker — Demo",
            "Other Establishment Services",
        ],
    )

    if module == "Past Accumulation File Upload — Demo":

        st.write(
            "### Upload Demo File"
        )

        uploaded = st.file_uploader(
            "Choose a CSV file",
            type=["csv"],
        )

        if uploaded:

            try:

                df = pd.read_csv(uploaded)

                st.success(
                    "File loaded successfully."
                )

                st.dataframe(
                    df,
                    use_container_width=True,
                )

                if st.button(
                    "Validate Demo File"
                ):

                    st.success(
                        "Demo file validation successful."
                    )

            except Exception as ex:

                st.error(
                    f"Could not read file: {ex}"
                )

    elif module == "International Worker — Demo":

        st.write(
            "International Worker information"
        )

        passport = st.text_input(
            "Demo Passport Number"
        )

        country = st.selectbox(
            "Country",
            [
                "United States",
                "United Kingdom",
                "Singapore",
                "UAE",
                "Other",
            ],
        )

        if st.button(
            "Save International Worker — Demo"
        ):

            add_log(
                "International Worker demo record saved"
            )

            st.success(
                "Demo record saved."
            )

    elif module == "ABRY — Demo":

        st.info(
            "ABRY module is represented here as a "
            "training simulation only."
        )

        if st.button(
            "Create ABRY Demo Application"
        ):

            add_log(
                "ABRY demo application created"
            )

            st.success(
                "Demo ABRY application created."
            )

    elif module == "Exemption — Demo":

        st.info(
            "Exemption functionality is simulated."
        )

        if st.button(
            "Create Exemption Demo Request"
        ):

            add_log(
                "Exemption demo request created"
            )

            st.success(
                "Demo exemption request created."
            )

    else:

        st.info(
            "Additional establishment-specific "
            "services can be represented here."
        )


# ============================================================
# Settings / Reset
# ============================================================

elif menu == "⚙️ Settings / Reset":

    st.subheader("Demo Settings")

    st.warning(
        "Resetting the demo deletes all changes made "
        "during this Streamlit session."
    )

    if st.button(
        "🗑️ Reset Demo Data",
        type="primary",
    ):

        for key in list(st.session_state.keys()):
            del st.session_state[key]

        st.rerun()

    st.divider()

    st.write("### Demo Information")

    st.write(
        """
        **Login**

        User ID: `DEMOEMP001`

        Password: `demo123`

        Captcha: `DEMO`

        **Demo Establishment**

        ABC Technologies Pvt. Ltd.

        **Demo Establishment Code**

        DLCPM0001234000
        """
    )


# ============================================================
# Footer
# ============================================================

st.divider()

st.caption(
    "EPFO Employer Portal — Training Demo | "
    "Not an official EPFO application | "
    "No real credentials, OTP, Aadhaar, PAN or payment data should be entered."
)
