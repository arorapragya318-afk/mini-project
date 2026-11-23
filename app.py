from flask import Flask, render_template, request, redirect, url_for, session
import mysql.connector
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = "change-this-to-a-long-random-secret"


# Database Connection
def get_db_connection():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="ABESIT@123456_3sem",
        database="online_voting"
    )


# Home Page
@app.route("/")
def home():
    return render_template("index.html")


# Voter Registration
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form["name"].strip()
        email = request.form["email"].strip().lower()
        password = request.form["password"]

        if not name or not email or len(password) < 8:
            return """
                <h2>Invalid Details</h2>
                <p>Please enter your name, email and a password
                containing at least 8 characters.</p>
                <a href="/register">Try Again</a>
            """

        connection = None
        cursor = None

        try:
            connection = get_db_connection()
            cursor = connection.cursor()

            hashed_password = generate_password_hash(password)

            query = """
                INSERT INTO voters (full_name, email, password)
                VALUES (%s, %s, %s)
            """

            cursor.execute(query, (name, email, hashed_password))
            connection.commit()

            return """
                <h2>Registration Successful!</h2>
                <p>Your voter account has been created.</p>
                <a href="/login">Go to Login</a>
            """

        except mysql.connector.IntegrityError:
            return """
                <h2>Email Already Registered!</h2>
                <a href="/login">Go to Login</a>
            """

        except mysql.connector.Error as error:
            return f"Database error: {error}"

        finally:
            if cursor is not None:
                cursor.close()

            if connection is not None and connection.is_connected():
                connection.close()

    return render_template("register.html")


# Voter Login
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"].strip().lower()
        password = request.form["password"]

        connection = None
        cursor = None

        try:
            connection = get_db_connection()
            cursor = connection.cursor(dictionary=True)

            query = "SELECT * FROM voters WHERE email = %s"
            cursor.execute(query, (email,))
            voter = cursor.fetchone()

            if voter and check_password_hash(voter["password"], password):
                session.clear()
                session["voter_id"] = voter["id"]
                session["voter_name"] = voter["full_name"]

                return redirect(url_for("dashboard"))

            return """
                <h2>Invalid Email or Password</h2>
                <a href="/login">Try Again</a>
            """

        except mysql.connector.Error as error:
            return f"Database error: {error}"

        finally:
            if cursor is not None:
                cursor.close()

            if connection is not None and connection.is_connected():
                connection.close()

    return render_template("login.html")

# View Candidates
# View Candidates
@app.route("/candidates")
def candidates():
    if "voter_id" not in session:
        return redirect(url_for("login"))

    connection = None
    cursor = None

    try:
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)

        # Get currently active elections
        cursor.execute("""
            SELECT id, election_name, description, start_date, end_date
            FROM elections
            WHERE status = 'Active'
            AND CURDATE() BETWEEN start_date AND end_date
            ORDER BY id DESC
        """)

        election_list = cursor.fetchall()

        election_id = request.args.get("election_id", type=int)

        # If no election is selected, show available elections
        if election_id is None:
            return render_template(
                "candidates.html",
                candidates=[],
                elections=election_list,
                selected_election=None,
                has_voted=False
            )

        # Verify selected election is active
        selected_election = next(
            (e for e in election_list if e["id"] == election_id),
            None
        )

        if selected_election is None:
            return "This election is not currently active."

        # Check whether voter has already voted in this election
        cursor.execute("""
            SELECT id
            FROM votes
            WHERE voter_id = %s AND election_id = %s
        """, (session["voter_id"], election_id))

        has_voted = cursor.fetchone() is not None

        # Get candidates of selected election only
        cursor.execute("""
            SELECT id, name, party
            FROM candidates
            WHERE election_id = %s
            ORDER BY id ASC
        """, (election_id,))

        candidate_list = cursor.fetchall()

        return render_template(
            "candidates.html",
            candidates=candidate_list,
            elections=election_list,
            selected_election=selected_election,
            has_voted=has_voted
        )

    except mysql.connector.Error as error:
        return f"Database error: {error}"

    finally:
        if cursor is not None:
            cursor.close()

        if connection is not None and connection.is_connected():
            connection.close()
            # Cast Vote
@app.route("/vote", methods=["POST"])
def vote():
    if "voter_id" not in session:
        return redirect(url_for("login"))

    candidate_id = request.form.get("candidate_id", type=int)
    election_id = request.form.get("election_id", type=int)

    if candidate_id is None or election_id is None:
        return "Invalid candidate or election selection."

    connection = None
    cursor = None

    try:
        connection = get_db_connection()
        connection.start_transaction()

        cursor = connection.cursor(dictionary=True)

        # Lock voter record to prevent simultaneous voting
        cursor.execute(
            "SELECT id FROM voters WHERE id = %s FOR UPDATE",
            (session["voter_id"],)
        )

        voter = cursor.fetchone()

        if voter is None:
            connection.rollback()
            session.clear()
            return redirect(url_for("login"))

        # Check whether election is active
        cursor.execute("""
            SELECT id
            FROM elections
            WHERE id = %s
            AND status = 'Active'
            AND CURDATE() BETWEEN start_date AND end_date
        """, (election_id,))

        election = cursor.fetchone()

        if election is None:
            connection.rollback()
            return "This election is not currently active."

        # Verify candidate belongs to this election
        cursor.execute("""
            SELECT id
            FROM candidates
            WHERE id = %s AND election_id = %s
        """, (candidate_id, election_id))

        candidate = cursor.fetchone()

        if candidate is None:
            connection.rollback()
            return "Invalid candidate for this election."

        # Check whether voter has already voted in this election
        cursor.execute("""
            SELECT id
            FROM votes
            WHERE voter_id = %s AND election_id = %s
        """, (session["voter_id"], election_id))

        existing_vote = cursor.fetchone()

        if existing_vote:
            connection.rollback()
            return """
                <h2>You have already voted in this election!</h2>
                <a href="/dashboard">Back to Dashboard</a>
            """

        # Save vote in votes table
        cursor.execute("""
            INSERT INTO votes (voter_id, candidate_id, election_id)
            VALUES (%s, %s, %s)
        """, (session["voter_id"], candidate_id, election_id))

        # Update candidate vote count
        cursor.execute("""
            UPDATE candidates
            SET votes = votes + 1
            WHERE id = %s
        """, (candidate_id,))

        connection.commit()

        return f"""
            <h2>Vote Submitted Successfully!</h2>
            <p>Thank you for participating in this election.</p>
            <a href="/results?election_id={election_id}">View Results</a>
            <br><br>
            <a href="/dashboard">Back to Dashboard</a>
        """

    except mysql.connector.Error as error:
        if connection is not None and connection.is_connected():
            connection.rollback()

        return f"Database error: {error}"

    finally:
        if cursor is not None:
            cursor.close()

        if connection is not None and connection.is_connected():
            connection.close()
# Voter Dashboard
@app.route("/dashboard")
def dashboard():
    if "voter_id" not in session:
        return redirect(url_for("login"))

    return render_template(
        "dashboard.html",
        name=session["voter_name"]
    )


# Logout
@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("home"))



# Election Results
@app.route("/results")
def results():

    if "voter_id" not in session and "admin_id" not in session:
        return redirect(url_for("login"))

    connection = None
    cursor = None

    try:
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)

        election_id = request.args.get("election_id", type=int)

        # If no election is selected, get the latest election
        if election_id is None:
            cursor.execute("""
                SELECT id
                FROM elections
                ORDER BY id DESC
                LIMIT 1
            """)
            election = cursor.fetchone()

            if election is None:
                return "No elections available."

            election_id = election["id"]

        # Verify election exists
        cursor.execute("""
            SELECT id, election_name
            FROM elections
            WHERE id = %s
        """, (election_id,))

        selected_election = cursor.fetchone()

        if selected_election is None:
            return "Election not found."

        # Get candidates of selected election only
        cursor.execute("""
            SELECT name, party, votes
            FROM candidates
            WHERE election_id = %s
            ORDER BY votes DESC, name ASC
        """, (election_id,))

        candidate_results = cursor.fetchall()

        # Calculate total votes
        total_votes = sum(candidate["votes"] for candidate in candidate_results)

        # Calculate percentage
        for candidate in candidate_results:
            if total_votes > 0:
                candidate["percentage"] = round(
                    candidate["votes"] / total_votes * 100, 2
                )
            else:
                candidate["percentage"] = 0

        return render_template(
            "results.html",
            results=candidate_results,
            total_votes=total_votes,
            selected_election=selected_election
        )

    except mysql.connector.Error as error:
        return f"Database error: {error}"

    finally:
        if cursor is not None:
            cursor.close()

        if connection is not None and connection.is_connected():
            connection.close()
# Admin Login
@app.route("/admin-login", methods=["GET", "POST"])
def admin_login():

    error = None

    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]

        connection = None
        cursor = None

        try:
            connection = get_db_connection()
            cursor = connection.cursor(dictionary=True)

            cursor.execute(
                "SELECT * FROM admin_users WHERE email = %s",
                (email,)
            )

            admin = cursor.fetchone()

            if admin and check_password_hash(admin["password"], password):
                session["admin_id"] = admin["id"]
                session["admin_name"] = admin["name"]

                return redirect(url_for("admin_dashboard"))

            else:
                error = "Invalid email or password!"

        except mysql.connector.Error as e:
            error = "Database error: " + str(e)

        finally:
            if cursor is not None:
                cursor.close()

            if connection is not None and connection.is_connected():
                connection.close()

    return render_template("admin_login.html", error=error)

# Admin Dashboard
@app.route("/admin-dashboard")
def admin_dashboard():

    if "admin_id" not in session:
        return redirect(url_for("admin_login"))

    return render_template(
        "admin_dashboard.html",
        name=session["admin_name"]
    )

# Add Candidate
@app.route("/admin-add-candidate", methods=["POST"])
def admin_add_candidate():

    if "admin_id" not in session:
        return redirect(url_for("admin_login"))

    name = request.form["name"]
    party = request.form["party"]
    election_id = request.form.get("election_id", type=int)

    if not election_id:
        return "Please select an election."

    connection = None
    cursor = None

    try:
        connection = get_db_connection()
        cursor = connection.cursor()

        # Check whether election exists
        cursor.execute(
            "SELECT id FROM elections WHERE id = %s",
            (election_id,)
        )

        election = cursor.fetchone()

        if election is None:
            return "Invalid election selected."

        # Add candidate to selected election
        cursor.execute("""
            INSERT INTO candidates
            (name, party, votes, election_id)
            VALUES (%s, %s, %s, %s)
        """, (name, party, 0, election_id))

        connection.commit()

        return redirect(url_for("admin_candidates"))

    except mysql.connector.Error as error:
        return f"Database error: {error}"

    finally:
        if cursor is not None:
            cursor.close()

        if connection is not None and connection.is_connected():
            connection.close()
# Delete Candidate
@app.route("/admin-delete-candidate/<int:candidate_id>", methods=["POST"])
def admin_delete_candidate(candidate_id):

    if "admin_id" not in session:
        return redirect(url_for("admin_login"))

    connection = None
    cursor = None

    try:
        connection = get_db_connection()
        cursor = connection.cursor()

        cursor.execute(
            "DELETE FROM candidates WHERE id = %s",
            (candidate_id,)
        )

        connection.commit()

        return redirect(url_for("admin_candidates"))

    except mysql.connector.Error as error:
        return f"Database error: {error}"

    finally:
        if cursor is not None:
            cursor.close()

        if connection is not None and connection.is_connected():
            connection.close()

# Update Candidate
@app.route("/admin-update-candidate/<int:candidate_id>", methods=["POST"])
def admin_update_candidate(candidate_id):

    if "admin_id" not in session:
        return redirect(url_for("admin_login"))

    name = request.form["name"]
    party = request.form["party"]

    connection = None
    cursor = None

    try:
        connection = get_db_connection()
        cursor = connection.cursor()

        cursor.execute("""
            UPDATE candidates
            SET name = %s, party = %s
            WHERE id = %s
        """, (name, party, candidate_id))

        connection.commit()

        return redirect(url_for("admin_candidates"))

    except mysql.connector.Error as error:
        return f"Database error: {error}"

    finally:
        if cursor is not None:
            cursor.close()

        if connection is not None and connection.is_connected():
            connection.close()

# Admin Manage Candidates
@app.route("/admin-candidates")
def admin_candidates():

    if "admin_id" not in session:
        return redirect(url_for("admin_login"))

    connection = None
    cursor = None

    try:
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)

        cursor.execute("""
            SELECT candidates.id, candidates.name,
       candidates.party, candidates.votes,
       elections.election_name
FROM candidates
LEFT JOIN elections
ON candidates.election_id = elections.id
ORDER BY candidates.id ASC
        """)

        candidate_list = cursor.fetchall()

        # Get all elections for candidate selection
        cursor.execute("""
            SELECT id, election_name
            FROM elections
            ORDER BY id DESC
        """)

        election_list = cursor.fetchall()

        return render_template(
            "admin_candidates.html",
            candidates=candidate_list,
            elections=election_list
        )

    except mysql.connector.Error as error:
        return f"Database error: {error}"

    finally:
        if cursor is not None:
            cursor.close()

        if connection is not None and connection.is_connected():
            connection.close()
            # Add Election
@app.route("/admin-add-election", methods=["POST"])
def admin_add_election():

    if "admin_id" not in session:
        return redirect(url_for("admin_login"))

    election_name = request.form["election_name"]
    description = request.form["description"]
    start_date = request.form["start_date"]
    end_date = request.form["end_date"]

    connection = None
    cursor = None

    try:
        connection = get_db_connection()
        cursor = connection.cursor()

        cursor.execute("""
            INSERT INTO elections
            (election_name, description, start_date, end_date, status)
            VALUES (%s, %s, %s, %s, %s)
        """, (
            election_name,
            description,
            start_date,
            end_date,
            "Upcoming"
        ))

        connection.commit()

        return redirect(url_for("admin_elections"))

    except mysql.connector.Error as error:
        return f"Database error: {error}"

    finally:
        if cursor is not None:
            cursor.close()

        if connection is not None and connection.is_connected():
            connection.close()

            # Delete Election
@app.route("/admin-delete-election/<int:election_id>", methods=["POST"])
def admin_delete_election(election_id):

    if "admin_id" not in session:
        return redirect(url_for("admin_login"))

    connection = None
    cursor = None

    try:
        connection = get_db_connection()
        cursor = connection.cursor()

        cursor.execute(
            "DELETE FROM elections WHERE id = %s",
            (election_id,)
        )

        connection.commit()

        return redirect(url_for("admin_elections"))

    except mysql.connector.Error as error:
        return f"Database error: {error}"

    finally:
        if cursor is not None:
            cursor.close()

        if connection is not None and connection.is_connected():
            connection.close()

            # Admin Update Election
@app.route("/admin-update-election/<int:election_id>", methods=["POST"])
def admin_update_election(election_id):

    if "admin_id" not in session:
        return redirect(url_for("admin_login"))

    election_name = request.form["election_name"]
    description = request.form["description"]
    start_date = request.form["start_date"]
    end_date = request.form["end_date"]
    status = request.form["status"]

    # Validate election status
    if status not in ["Upcoming", "Active", "Completed"]:
        return "Invalid election status."

    if start_date > end_date:
        return "End date cannot be before start date."

    connection = None
    cursor = None

    try:
        connection = get_db_connection()
        cursor = connection.cursor()

        cursor.execute("""
            UPDATE elections
            SET election_name = %s,
                description = %s,
                start_date = %s,
                end_date = %s,
                status = %s
            WHERE id = %s
        """, (
            election_name,
            description,
            start_date,
            end_date,
            status,
            election_id
        ))

        connection.commit()

        return redirect(url_for("admin_elections"))

    except mysql.connector.Error as error:
        if connection is not None and connection.is_connected():
            connection.rollback()

        return f"Database error: {error}"

    finally:
        if cursor is not None:
            cursor.close()

        if connection is not None and connection.is_connected():
            connection.close()
            # Admin Manage Elections
@app.route("/admin-elections")
def admin_elections():

    if "admin_id" not in session:
        return redirect(url_for("admin_login"))

    connection = None
    cursor = None

    try:
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)

        cursor.execute("""
            SELECT * FROM elections
            ORDER BY id DESC
        """)

        election_list = cursor.fetchall()

        return render_template(
            "admin_elections.html",
            elections=election_list
        )

    except mysql.connector.Error as error:
        return f"Database error: {error}"

    finally:
        if cursor is not None:
            cursor.close()

        if connection is not None and connection.is_connected():
            connection.close()

            # Admin Voter Records
@app.route("/admin-voters")
def admin_voters():

    if "admin_id" not in session:
        return redirect(url_for("admin_login"))

    connection = None
    cursor = None

    try:
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)

        cursor.execute("""
            SELECT id, full_name, email, has_voted
            FROM voters
            ORDER BY id ASC
        """)

        voter_list = cursor.fetchall()

        return render_template(
            "admin_voters.html",
            voters=voter_list
        )

    except mysql.connector.Error as error:
        return f"Database error: {error}"

    finally:
        if cursor is not None:
            cursor.close()

        if connection is not None and connection.is_connected():
            connection.close()

# Admin Logout
@app.route("/admin-logout")
def admin_logout():
    session.pop("admin_id", None)
    session.pop("admin_name", None)
    return redirect(url_for("admin_login"))

# Test Database Connection
@app.route("/test-db")
def test_db():
    connection = None

    try:
        connection = get_db_connection()
        return "MySQL Database Connected Successfully!"

    except mysql.connector.Error as error:
        return f"MySQL Error: {error}"

    finally:
        if connection is not None and connection.is_connected():
            connection.close()


# Run Flask Application
if __name__ == "__main__":
    app.run(debug=True)
   