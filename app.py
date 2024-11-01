import re
from flask import Flask, render_template,request,session,redirect,flash,url_for,jsonify
from config import Database
import random

app = Flask(__name__)

app.secret_key = 'your_secret_key'
# Initialize Database
db = Database()

#Guest Block

@app.route("/")
def home():
    return render_template("guest/index.html")

@app.route("/index")
def index():
    return render_template("guest/index.html")

@app.route("/logout")
def logout():
    # Clear the session data
    session.clear()
    flash("You have been logged out.", "info")
    return redirect(url_for('login'))

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form['username']
        password = request.form['password']

        # Fetch user from the database
        query = f"SELECT * FROM tbl_login WHERE username = '{username}' and password='{password}'"
        user = db.fetchone(query)

        if user:
            session['user_id'] = user['id']
            # Verify the password
            if user['type']=='admin':
                flash("Login successful!", "success")
                return redirect(url_for('adminhome'))  
            elif user['type']=='student':
                flash("Login successful!", "success")
                return redirect(url_for('studenthome'))
            elif user['type']=='staff':
                flash("Login successful!", "success")
                return redirect(url_for('staffhome'))
            else:
                flash("Invalid username or password.", "danger")
            
        else:
            flash("User not found.", "danger")

    return render_template("guest/login.html")

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        # Get form data
        name = request.form['name']
        course = request.form['course']
        details = request.form['details']
        username = request.form['username']
        password = request.form['password']
        

        try:
            # Insert into tbl_login
            insert_login_query = f"""
            INSERT INTO tbl_login (username, password, type) 
            VALUES ('{username}', '{password}', 'student')
            """
            db.single_insert(insert_login_query)

            # Retrieve the login ID
            get_login_id_query = f"SELECT id FROM tbl_login WHERE username = '{username}'"
            login_record = db.fetchone(get_login_id_query)
            login_id = login_record['id']

            # Insert into registration table
            insert_registration_query = f"""
            INSERT INTO tbl_student (login_id, name,course, details) 
            VALUES ({login_id}, '{name}', '{course}', '{details}')
            """
            print(insert_registration_query)
            db.single_insert(insert_registration_query)

            flash("Registration successful!", "success")
            return redirect(url_for('login'))
        except Exception as e:
            flash(f"Registration failed: {str(e)}", "danger")
            
    courses=db.fetchall("select * from tbl_course")

    return render_template("guest/register.html",courses=courses)


#admin Block

@app.route("/admin-home")
def adminhome():
    
    course = db.fetchone("SELECT COUNT(*) as count FROM tbl_course")
    subject = db.fetchone("SELECT COUNT(*) as count FROM tbl_subject")
    staff = db.fetchone("SELECT COUNT(*) as count FROM tbl_staff")
    assignment = db.fetchone("SELECT COUNT(*) as count FROM tbl_assignment")

    
    data = {
        "course": course,
        "subject": subject,
        "staff": staff,
        "assignment": assignment
    }

    
    return render_template("admin/index.html", data=data)



@app.route("/admin-course", methods=["GET","POST"])
def admincourse():
    if request.method == "POST":
        course_id = request.form.get('course_id')
        course_name = request.form['course']
      

        if course_id:  # Update operation
            try:
                update_course_query = f"""
                UPDATE tbl_course 
                SET course_name = '{course_name}'
                WHERE id = {course_id}
                """
                db.execute(update_course_query)
                flash("course updated successfully!", "success")
            except Exception as e:
                flash(f"Failed to update course: {str(e)}", "danger")
        else:  # Create operation
            try:
                insert_course_query = f"""
                INSERT INTO tbl_course (course_name) 
                VALUES ('{course_name}')
                """
                db.single_insert(insert_course_query)
                flash("course added successfully!", "success")
            except Exception as e:
                flash(f"Failed to add course: {str(e)}", "danger")
        
        return redirect(url_for('admincourse'))

    # Fetch all categories and the course to edit (if any)
    courses = db.fetchall("SELECT * FROM tbl_course")
    course_to_edit = None
    if 'edit' in request.args:
        course_id = request.args.get('edit')
        course_to_edit = db.fetchone(f"SELECT * FROM tbl_course WHERE id = {course_id}")
    
    return render_template("admin/course.html", courses=courses, course_to_edit=course_to_edit)

@app.route("/delete-course/<int:course_id>", methods=["POST"])
def delete_course(course_id):
    try:
        delete_query = f"DELETE FROM tbl_course WHERE id = {course_id}"
        db.execute(delete_query)
        flash("course deleted successfully!", "success")
    except Exception as e:
        flash(f"Failed to delete course: {str(e)}", "danger")
    
    return redirect(url_for('admincourse'))



@app.route("/admin-staff", methods=["GET", "POST"])
def adminstaff():
    if request.method == "POST":
        staff_id = request.form.get('staff_id')  # For updates
        staff_name = request.form['staff']
        staff_details = request.form['details']
        username = request.form['username']
        password = request.form['password']

        if staff_id:  # Update operation for both staff and login details
            try:
                # Update staff details
                update_staff_query = f"""
                UPDATE tbl_staff 
                SET staff_name = '{staff_name}', staff_details = '{staff_details}'
                WHERE id = {staff_id}
                """
                db.execute(update_staff_query)

                # Update login details associated with this staff
                update_login_query = f"""
                UPDATE tbl_login 
                SET username = '{username}', password = '{password}'
                WHERE id = (SELECT login_id FROM tbl_staff WHERE id = {staff_id})
                """
                db.execute(update_login_query)

                flash("Staff and login details updated successfully!", "success")
            except Exception as e:
                flash(f"Failed to update staff: {str(e)}", "danger")
        else:  # Create operation for both tables
            try:
                # Insert into tbl_login
                insert_staff_login = f"""
                INSERT INTO tbl_login (username, password, type) 
                VALUES ('{username}', '{password}', 'staff')
                """
                login_insert = db.executeAndReturnId(insert_staff_login)

                # Insert into tbl_staff after login insert
                if login_insert:
                    insert_staff_query = f"""
                    INSERT INTO tbl_staff (staff_name, staff_details, login_id) 
                    VALUES ('{staff_name}', '{staff_details}', '{login_insert}')
                    """
                    db.single_insert(insert_staff_query)
                    flash("Staff added successfully!", "success")
            except Exception as e:
                flash(f"Failed to add staff: {str(e)}", "danger")

        return redirect(url_for('adminstaff'))

    # Fetch all staff records and any staff to edit
    staffs = db.fetchall("SELECT * FROM tbl_staff")
    staff_to_edit = None
    if 'edit' in request.args:
        staff_id = request.args.get('edit')
        staff_to_edit = db.fetchone(f"SELECT s.*,l.username,l.password FROM tbl_staff s inner join tbl_login l on l.id=s.login_id WHERE s.id = {staff_id}")
    
    return render_template("admin/staff.html", staffs=staffs, staff_to_edit=staff_to_edit)


@app.route("/delete-staff/<int:staff_id>", methods=["POST"])
def delete_staff(staff_id):
    try:
        delete_query = f"DELETE FROM tbl_staff WHERE id = {staff_id}"
        db.execute(delete_query)
        flash("staff deleted successfully!", "success")
    except Exception as e:
        flash(f"Failed to delete staff: {str(e)}", "danger")
    
    return redirect(url_for('adminstaff'))


@app.route("/admin-subject", methods=["GET", "POST"])
def adminsubject():
    if request.method == "POST":
        subject_id = request.form.get('subject_id')
        subject_name = request.form['subject']
        course_id = request.form['course_id']

        if subject_id:  # Update operation
            try:
                update_subject_query = f"""
                UPDATE tbl_subject 
                SET subject_name = '{subject_name}', course_id = {course_id}
                WHERE id = {subject_id}
                """
                db.execute(update_subject_query)
                flash("Subject updated successfully!", "success")
            except Exception as e:
                flash(f"Failed to update subject: {str(e)}", "danger")
        else:  # Create operation
            try:
                insert_subject_query = f"""
                INSERT INTO tbl_subject (subject_name, course_id) 
                VALUES ('{subject_name}', {course_id})
                """
                db.single_insert(insert_subject_query)
                flash("Subject added successfully!", "success")
            except Exception as e:
                flash(f"Failed to add subject: {str(e)}", "danger")
        
        return redirect(url_for('adminsubject'))
    
    courses = db.fetchall("SELECT * FROM tbl_course")
    # Fetch all subjects and the subject to edit (if any)
    subjects = db.fetchall("SELECT *,s.id as sub_id FROM tbl_subject s inner join tbl_course c on c.id=s.course_id")
    subject_to_edit = None
    if 'edit' in request.args:
        subject_id = request.args.get('edit')
        subject_to_edit = db.fetchone(f"SELECT * FROM tbl_subject WHERE id = {subject_id}")
    
    return render_template("admin/subject.html", subjects=subjects, subject_to_edit=subject_to_edit,courses=courses)

@app.route("/delete-subject/<int:subject_id>", methods=["POST"])
def delete_subject(subject_id):
    try:
        delete_query = f"DELETE FROM tbl_subject WHERE id = {subject_id}"
        db.execute(delete_query)
        flash("Subject deleted successfully!", "success")
    except Exception as e:
        flash(f"Failed to delete subject: {str(e)}", "danger")
    
    return redirect(url_for('adminsubject'))


@app.route("/admin-period", methods=["GET", "POST"])
def adminperiod():
    if request.method == "POST":
        period_id = request.form.get('period_id')
        day = request.form['day']
        period = request.form['period']
        time = request.form['time']

        if period_id:  # Update operation
            try:
                update_period_query = f"""
                UPDATE tbl_period 
                SET day = '{day}', period = '{period}', time = '{time}'
                WHERE id = {period_id}
                """
                db.execute(update_period_query)
                flash("Period updated successfully!", "success")
            except Exception as e:
                flash(f"Failed to update period: {str(e)}", "danger")
        else:  # Create operation
            try:
                 # Check if the combination exists
                check_combination_query = """
                SELECT COUNT(*) FROM tbl_period
                WHERE day = %s AND period = %s
                """
                existing_combination = db.fetchone(check_combination_query.format(), (day, period))[0]

                insert_period_query = f"""
                INSERT INTO tbl_period (day, period, time) 
                VALUES ('{day}', '{period}', '{time}')
                """
                db.single_insert(insert_period_query)
                flash("Period added successfully!", "success")
            except Exception as e:
                flash(f"Failed to add period: {str(e)}", "danger")
        
        return redirect(url_for('adminperiod'))
    
    # Fetch all periods and the period to edit (if any)
    periods = db.fetchall("SELECT * FROM tbl_period")
    period_to_edit = None
    if 'edit' in request.args:
        period_id = request.args.get('edit')
        period_to_edit = db.fetchone(f"SELECT * FROM tbl_period WHERE id = {period_id}")
    
    return render_template("admin/period.html", periods=periods, period_to_edit=period_to_edit)

@app.route("/delete-period/<int:period_id>", methods=["POST"])
def delete_period(period_id):
    try:
        delete_query = f"DELETE FROM tbl_period WHERE id = {period_id}"
        db.execute(delete_query)
        flash("Period deleted successfully!", "success")
    except Exception as e:
        flash(f"Failed to delete period: {str(e)}", "danger")
    
    return redirect(url_for('adminperiod'))


@app.route("/admin-assign-subject", methods=["GET", "POST"])
def adminassignsubject():
    if request.method == "POST":
        assign_id = request.form.get('assign_id')
        staff_id = request.form['staff_id']
        subject_id = request.form['subject_id']

        if assign_id: 
            try:
                update_assign_query = f"""
                UPDATE tbl_assign_subject 
                SET staff_id = {staff_id}, subject_id = {subject_id}
                WHERE id = {assign_id}
                """
                db.execute(update_assign_query)
                flash("Assignment updated successfully!", "success")
            except Exception as e:
                flash(f"Failed to update assignment: {str(e)}", "danger")
        else:  # Create operation
            try:
                insert_assign_query = f"""
                INSERT INTO tbl_assign_subject (staff_id, subject_id) 
                VALUES ({staff_id}, {subject_id})
                """
                db.single_insert(insert_assign_query)
                flash("Assignment added successfully!", "success")
            except Exception as e:
                flash(f"Failed to add assignment: {str(e)}", "danger")
        
        return redirect(url_for('adminassignsubject'))
    
    # Fetch all staff members and subjects for dropdowns
    staff_members = db.fetchall("SELECT * FROM tbl_staff")
    subjects = db.fetchall("SELECT * FROM tbl_subject")

    # Fetch all assigned subjects and the assignment to edit (if any)
    assigned_subjects = db.fetchall("""
        SELECT a.id, s.staff_name as staff_name, subj.subject_name 
        FROM tbl_assign_subject a 
        JOIN tbl_staff s ON a.staff_id = s.id
        JOIN tbl_subject subj ON a.subject_id = subj.id
    """)
    
    assign_to_edit = None
    if 'edit' in request.args:
        assign_id = request.args.get('edit')
        assign_to_edit = db.fetchone(f"SELECT * FROM tbl_assign_subject WHERE id = {assign_id}")
    
    return render_template("admin/assign_subject.html", assigned_subjects=assigned_subjects, assign_to_edit=assign_to_edit, staff_members=staff_members, subjects=subjects)

@app.route("/delete-assign-subject/<int:assign_id>", methods=["POST"])
def delete_assign_subject(assign_id):
    try:
        delete_query = f"DELETE FROM tbl_assign_subject WHERE id = {assign_id}"
        db.execute(delete_query)
        flash("Assignment deleted successfully!", "success")
    except Exception as e:
        flash(f"Failed to delete assignment: {str(e)}", "danger")
    
    return redirect(url_for('adminassignsubject'))


@app.route("/admin-generate-timetable", methods=["POST"])
def generate_timetable():
    try:
        db.execute("TRUNCATE TABLE tbl_timetable")  # Clear previous timetable

        # Fetch all courses
        courses = db.fetchall("SELECT * FROM tbl_course")

        # Dictionary to track staff assignments by day and period
        staff_schedule = {}

        for course in courses:
            # Fetch subjects for the course
            subjects = db.fetchall(f"SELECT * FROM tbl_subject WHERE course_id={course['id']}")

            # Fetch all periods (days and time slots)
            periods = db.fetchall("SELECT * FROM tbl_period")

            # Loop through each period for timetable generation
            for period in periods:
                assigned = False  # Flag to track if a subject has been assigned
                attempts = 0  # Counter to prevent infinite loops
                max_attempts = 10  # Set a limit on the number of attempts to avoid infinite loops

                while attempts < max_attempts:
                    # Select a random subject
                    selected_subject = random.choice(subjects)

                    # Fetch available staff for the selected subject
                    staffs = db.fetchall(f"SELECT staff_id FROM tbl_assign_subject WHERE subject_id={selected_subject['id']}")

                    # If staff are available, proceed to assign them
                    if staffs:
                        # Get the day and period as a key to track staff assignment
                        day_period_key = (period['day'], period['period'])

                        # Initialize the staff schedule for this period if not already done
                        if day_period_key not in staff_schedule:
                            staff_schedule[day_period_key] = set()

                        # Try to assign a staff member who isn't already assigned to this period
                        for staff in staffs:
                            selected_staff_id = staff['staff_id']

                            if selected_staff_id not in staff_schedule[day_period_key]:
                                # Assign the staff to this period
                                staff_schedule[day_period_key].add(selected_staff_id)

                                # Insert the timetable entry
                                db.execute(f"""
                                    INSERT INTO tbl_timetable (course_id, subject_id, staff_id, period_id)
                                    VALUES ({course['id']}, {selected_subject['id']}, {selected_staff_id}, {period['id']})
                                """)

                                assigned = True  # Mark as assigned
                                break  # Exit the loop after successful assignment
                        if assigned:
                            break  # Exit the while loop if assigned

                    attempts += 1  # Increment attempts

                if not assigned:
                    # If no staff was available after max attempts, handle the fallback
                    fallback_staff = random.choice(staffs)['staff_id'] if staffs else None
                    if fallback_staff:
                        # Insert the timetable entry with fallback
                        db.execute(f"""
                            INSERT INTO tbl_timetable (course_id, subject_id, staff_id, period_id)
                            VALUES ({course['id']}, {selected_subject['id']}, {fallback_staff}, {period['id']})
                        """)
                        staff_schedule[day_period_key].add(fallback_staff)

                        flash(f"Fallback: Assigned subject {selected_subject['subject_name']} with available staff for {period['day']} {period['period']}.", "warning")
                    else:
                        flash(f"No available staff for any subject during {period['day']} {period['period']}.", "error")

        flash("Timetable generated successfully.", "success")

    except Exception as e:
        logging.error(f"Error generating timetable: {str(e)}")
        flash(f"Error generating timetable: {str(e)}", "error")

    return redirect(url_for('admin_timetable'))
  

  




# Define constants for days and periods
DAYS = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']
PERIODS = ['first', 'second', 'third', 'forth']

@app.route("/admin-timetable")
def admin_timetable():
    # try:
    # Fetch all required data
    courses = db.fetchall("SELECT * FROM tbl_course")
    subjects = db.fetchall("SELECT * FROM tbl_subject")
    staff_members = db.fetchall("SELECT * FROM tbl_staff")

    # Fetch the complete timetable with all related information
    timetable_entries = db.fetchall("""
        SELECT 
            tt.id,
            tt.course_id,
            tt.period_id,
            tt.subject_id,
            tt.staff_id,
            p.day,
            p.period,
            s.subject_name,
            st.staff_name
        FROM tbl_timetable tt
        JOIN tbl_period p ON tt.period_id = p.id
        JOIN tbl_subject s ON tt.subject_id = s.id
        JOIN tbl_staff st ON tt.staff_id = st.id
        ORDER BY 
            FIELD(p.day, 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday'),
            FIELD(p.period, 'first', 'second', 'third', 'forth')
    """)

    # Organize timetable data for template
    organized_timetable = {course['id']: {period: {} for period in PERIODS} for course in courses}
    
    for entry in timetable_entries:
        organized_timetable[entry['course_id']][entry['period']][entry['day']] = {
            'id': entry['id'],
            'period_id': entry['period_id'],
            'subject_id': entry['subject_id'],
            'staff_id': entry['staff_id'],
            'subject': entry['subject_name'],
            'staff': entry['staff_name']
        }
    
    return render_template(
        "admin/timetable.html",
        courses=courses,
        timetables=organized_timetable,
        subjects={course['id']: [s for s in subjects if s['course_id'] == course['id']] for course in courses},
        staff_members=staff_members,
        days=DAYS,
        periods=PERIODS
    )



@app.route("/change-staff", methods=["GET","POST"])  
def changestaff():
    staff_subjects = None                        
    staff_id = request.args.get('staff_id')
    if staff_id:
        query=f"""SELECT tbl_assign_subject.subject_id, tbl_subject.subject_name  FROM tbl_assign_subject
                LEFT JOIN tbl_subject ON tbl_subject.id= tbl_assign_subject.subject_id
                WHERE tbl_assign_subject.staff_id={staff_id}"""
        staff_subjects=db.fetchall(query)
        print(f"staff_subjects:{staff_subjects}")

    if request.method == 'POST':
        id = request.form['id']
        date = request.form['date']
        period = request.form['period']
        course_id = request.form['course_id']
        staff =request.form['staff_name']
        subject = request.form['subject_name']
        print(f"id:{id},period:{period},course Id:{course_id}")
        if id:
            query = f"""UPDATE replace_staff SET date='{date}', replaced_staff='{staff}', period='{period}', replaced_subject='{subject}', course_id={course_id}
                        WHERE id={id}"""
            db.execute(query)
        else:
            query = f"""INSERT INTO replace_staff (date, replaced_staff, period, replaced_subject, course_id)
                    VALUES ('{date}', '{staff}', '{period}', '{subject}', {course_id})"""
            db.execute(query)

    replaced_staff_to_edit=None
    edit_staff_id = request.args.get('edit')
    if edit_staff_id:
        replaced_staff_to_edit=db.fetchone(f"""SELECT replace_staff.*, tbl_course.course_name AS course_name 
                                  FROM replace_staff
                                  LEFT JOIN tbl_course ON replace_staff.course_id=tbl_course.id
                                  WHERE replace_staff.id = {edit_staff_id}
                                  """)
    
        
    replaced_staff=db.fetchall(f"""SELECT replace_staff.*, tbl_course.course_name AS course_name 
                                  FROM replace_staff
                                  LEFT JOIN tbl_course ON replace_staff.course_id=tbl_course.id""")
    

    staffs   =db.fetchall("""SELECT id, staff_name FROM tbl_staff """)
    subjects =db.fetchall("""SELECT subject_name FROM tbl_subject""")
    course = db.fetchall(""" SELECT * FROM  tbl_course""")
    print(f"course:{course}")
    return render_template("admin/change_staff.html", staffs=staffs, subjects=subjects, course=course, replaced_staff = replaced_staff, replaced_staff_to_edit= replaced_staff_to_edit, staff_subjects=staff_subjects )

from flask import  jsonify
@app.route('/get_subjects', methods=['GET'])
def get_subjects():
    subjects = None                        
    staff_id = request.args.get('staff_id')
    course_id = request.args.get('course_id')
    print(f"course id:{course_id}")
    if staff_id:
        query=f"""SELECT tbl_assign_subject.subject_id, tbl_subject.subject_name  FROM tbl_assign_subject
                LEFT JOIN tbl_subject ON tbl_subject.id= tbl_assign_subject.subject_id
                WHERE tbl_assign_subject.staff_id={staff_id} AND tbl_subject.course_id={course_id}"""
        subjects=db.fetchall(query)
    print(f"staff_subjects:{subjects}")
    
    return jsonify(subjects)

@app.route('/get_period', methods=['GET'])
def get_period():
    print(f"staff_subject 1")
    period = None                        
    date = request.args.get('date')
    if date:
        try:
            
            
            parsed_date = datetime.strptime(date, '%Y-%m-%d')
            
            day_name = parsed_date.strftime("%A") 
            print(f"Day: {day_name}")

           
            query = f"""SELECT period FROM tbl_period WHERE day = '{day_name}'"""  
            period = db.fetchall(query) 
            print(f"period{period}")
            
        except ValueError:
            return jsonify({"error": "Invalid date format. Please use YYYY-MM-DD."}), 400
    
    
    return jsonify(period)

@app.route("/delete-replace-staff/<int:replace_id>", methods=["POST"])
def delete_replace_staff(replace_id):
    try:
        delete_query = f"DELETE FROM replace_staff WHERE id = {replace_id}"
        db.execute(delete_query)
        flash(" deleted successfully!", "success")
    except Exception as e:
        flash(f"Failed to delete assignment: {str(e)}", "danger")
    
    return redirect(url_for('changestaff'))


#staff Block

@app.route("/staff-home")
def staffhome():

    # Assuming you have the staff ID stored in the session
    staff_id = session.get('user_id')

    if not staff_id:
        return redirect(url_for('login'))  # Redirect to login if not logged in

    # Fetch staff-specific timetable entries
    timetable_entries = db.fetchall(f"""
        SELECT 
            tt.id,
            tt.course_id,
            cs.course_name,
            tt.period_id,
            tt.subject_id,
            tt.staff_id,
            p.day,
            p.period,
            s.subject_name,
            st.staff_name
        FROM tbl_timetable tt
        JOIN tbl_period p ON tt.period_id = p.id
        JOIN tbl_subject s ON tt.subject_id = s.id
        JOIN tbl_staff st ON tt.staff_id = st.id
        JOIN tbl_course cs on tt.course_id=cs.id
        WHERE tt.staff_id = {staff_id}
        ORDER BY 
            FIELD(p.day, 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday'),
            FIELD(p.period, 'first', 'second', 'third', 'forth')
    """)

    # Organize timetable data for the template
    organized_timetable = {period: {day: None for day in DAYS} for period in PERIODS}
    
    for entry in timetable_entries:
        organized_timetable[entry['period']][entry['day']] = {
            'id': entry['id'],
            'subject_id': entry['subject_id'],
            'subject_name': entry['subject_name'],
            'staff_name': entry['staff_name'],
            'course_name': entry['course_name']
        }
    
    return render_template(
        "staff/index.html",
        timetable=organized_timetable,
        days=DAYS,
        periods=PERIODS
    )




@app.route("/staff-assignment", methods=["GET", "POST"])
def staffassignment():
    staff_id = session.get('user_id')
    if request.method == "POST":
        assignment_id = request.form.get('assignment_id')
        subject_id = request.form['subject_id']
        student_id = request.form['student_id']
        description = request.form['description']
        due_date = request.form['due_date']

        if assignment_id:  # Update operation
            try:
                update_assignment_query = f"""
                UPDATE tbl_assignment 
                SET subject_id = {subject_id}, student_id = {student_id}, description = '{description}', due_date = '{due_date}'
                WHERE id = {assignment_id}
                """
                db.execute(update_assignment_query)
                flash("Assignment updated successfully!", "success")
            except Exception as e:
                flash(f"Failed to update assignment: {str(e)}", "danger")
        else:  # Create operation
            try:
                
                insert_assignment_query = f"""
                INSERT INTO tbl_assignment (subject_id, student_id, description, due_date,staff_id) 
                VALUES ({subject_id}, {student_id}, '{description}', '{due_date}','{staff_id}')
                """
                print(insert_assignment_query)
                db.single_insert(insert_assignment_query)
                flash("Assignment added successfully!", "success")
                return redirect(url_for('staffassignment'))
            except Exception as e:
                flash(f"Failed to add assignment: {str(e)}", "danger")
            
        
        
    
   

    # Fetch all students and subjects for dropdowns
    students = db.fetchall(f"SELECT st.login_id,st.name FROM tbl_subject s inner join tbl_assign_subject asb on asb.subject_id=s.id inner join tbl_student st on st.course=s.course_id where asb.staff_id={staff_id}")
    subjects = db.fetchall(f"SELECT s.* FROM tbl_subject s inner join tbl_assign_subject asb on asb.subject_id=s.id where asb.staff_id={staff_id}")

    # Fetch all assignments and the assignment to edit (if any)
    assignments = db.fetchall(f"""
        SELECT a.id, subj.subject_name, s.name as student_name, a.description, a.due_date, sf.staff_name
        FROM tbl_assignment a 
        JOIN tbl_subject subj ON a.subject_id = subj.id
        JOIN tbl_student s ON a.student_id = s.login_id join tbl_staff sf on sf.login_id=a.staff_id where a.staff_id={staff_id}
    """)
    
    assignment_to_edit = None
    if 'edit' in request.args:
        assignment_id = request.args.get('edit')
        assignment_to_edit = db.fetchone(f"SELECT * FROM tbl_assignment WHERE id = {assignment_id}")
    
    return render_template("staff/assignments.html", assignments=assignments, assignment_to_edit=assignment_to_edit, students=students, subjects=subjects)

@app.route("/staff-live-assignment", methods=["GET", "POST"])
def staffliveassignment():
    staff_id = session.get('user_id')
   
    # Fetch all assignments and the assignment to edit (if any)
    assignments = db.fetchall(f"""
        SELECT a.id, subj.subject_name, s.name as student_name, a.description, a.due_date, sf.staff_name
        FROM tbl_assignment a 
        JOIN tbl_subject subj ON a.subject_id = subj.id
        JOIN tbl_student s ON a.student_id = s.login_id join tbl_staff sf on sf.login_id=a.staff_id where a.staff_id={staff_id} and a.due_date>now()
    """)
    
  
    return render_template("staff/live_assignments.html", assignments=assignments)

@app.route("/staff-expired-assignment", methods=["GET", "POST"])
def staffexpiredassignment():
    staff_id = session.get('user_id')
   
    # Fetch all assignments and the assignment to edit (if any)
    assignments = db.fetchall(f"""
        SELECT a.id, subj.subject_name, s.name as student_name, a.description, a.due_date, sf.staff_name
        FROM tbl_assignment a 
        JOIN tbl_subject subj ON a.subject_id = subj.id
        JOIN tbl_student s ON a.student_id = s.login_id join tbl_staff sf on sf.login_id=a.staff_id where a.staff_id={staff_id} and a.due_date<=now()
    """)
    
  
    return render_template("staff/expired_assignments.html", assignments=assignments)



@app.route("/delete-assignment/<int:assignment_id>", methods=["POST"])
def delete_assignment(assignment_id):
    try:
        delete_query = f"DELETE FROM tbl_assignment WHERE id = {assignment_id}"
        db.execute(delete_query)
        flash("Assignment deleted successfully!", "success")
    except Exception as e:
        flash(f"Failed to delete assignment: {str(e)}", "danger")
    
    return redirect(url_for('staffassignment'))

@app.route("/staff-timetable", methods=["GET"])
def staff_timetable():
    # try:
    # Fetch all required data
    courses = db.fetchall("SELECT * FROM tbl_course")
    subjects = db.fetchall("SELECT * FROM tbl_subject")
    staff_members = db.fetchall("SELECT * FROM tbl_staff")

    # Fetch the complete timetable with all related information
    timetable_entries = db.fetchall("""
        SELECT 
            tt.id,
            tt.course_id,
            tt.period_id,
            tt.subject_id,
            tt.staff_id,
            p.day,
            p.period,
            s.subject_name,
            st.staff_name
        FROM tbl_timetable tt
        JOIN tbl_period p ON tt.period_id = p.id
        JOIN tbl_subject s ON tt.subject_id = s.id
        JOIN tbl_staff st ON tt.staff_id = st.id
        ORDER BY 
            FIELD(p.day, 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday'),
            FIELD(p.period, 'first', 'second', 'third', 'forth')
    """)

    # Organize timetable data for template
    organized_timetable = {course['id']: {period: {} for period in PERIODS} for course in courses}
    
    for entry in timetable_entries:
        organized_timetable[entry['course_id']][entry['period']][entry['day']] = {
            'id': entry['id'],
            'period_id': entry['period_id'],
            'subject_id': entry['subject_id'],
            'staff_id': entry['staff_id'],
            'subject': entry['subject_name'],
            'staff': entry['staff_name']
        }
    
    return render_template(
        "staff/timetable.html",
        courses=courses,
        timetables=organized_timetable,
        subjects={course['id']: [s for s in subjects if s['course_id'] == course['id']] for course in courses},
        staff_members=staff_members,
        days=DAYS,
        periods=PERIODS
    )
    
    
    
#student

@app.route("/student-home", methods=["GET"])
def studenthome():
    
    student_id = session.get('user_id')
    
    # Fetch the course ID for the logged-in student
    query = f"SELECT course FROM tbl_student WHERE login_id={student_id}"
    result = db.fetchone(query)  # Fetch the result as a dictionary or tuple
    
    if result:
        course_id = result['course']  # Extract the 'course' value if result is a dictionary
        print(f"course: {course_id}")
    
        # Get the current date
        today = datetime.today().strftime('%Y-%m-%d')  # Format as 'YYYY-MM-DD'

        # Modify the SQL query to fetch substitutions only for the current day
        select_query = f"""
            SELECT * FROM replace_staff 
            WHERE course_id = {course_id} 
            AND date = '{today}'
        """
        
        substitutions = db.fetchall(select_query)
        print(f"this is the substitutions :{substitutions}")
        




    # try:
    # Fetch all required data
    courses = db.fetchall(f"SELECT c.* FROM tbl_course c inner join tbl_student s on s.course=c.id where s.login_id={student_id} ")
    subjects = db.fetchall("SELECT * FROM tbl_subject")
    staff_members = db.fetchall("SELECT * FROM tbl_staff")

    # Fetch the complete timetable with all related information
    timetable_entries = db.fetchall(f"""
        SELECT 
            tt.id,
            tt.course_id,
            tt.period_id,
            tt.subject_id,
            tt.staff_id,
            p.day,
            p.period,
            s.subject_name,
            st.staff_name
        FROM tbl_timetable tt
        JOIN tbl_period p ON tt.period_id = p.id
        JOIN tbl_subject s ON tt.subject_id = s.id
        JOIN tbl_staff st ON tt.staff_id = st.id
        join tbl_student std on std.course=tt.course_id
        where std.login_id={student_id}
        ORDER BY 
            FIELD(p.day, 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday'),
            FIELD(p.period, 'first', 'second', 'third', 'forth')
    """)

    # Organize timetable data for template
    organized_timetable = {course['id']: {period: {} for period in PERIODS} for course in courses}
    
    for entry in timetable_entries:
        organized_timetable[entry['course_id']][entry['period']][entry['day']] = {
            'id': entry['id'],
            'period_id': entry['period_id'],
            'subject_id': entry['subject_id'],
            'staff_id': entry['staff_id'],
            'subject': entry['subject_name'],
            'staff': entry['staff_name']
        }
    
    return render_template(
        "student/index.html",
        courses=courses,
        timetables=organized_timetable,
        subjects={course['id']: [s for s in subjects if s['course_id'] == course['id']] for course in courses},
        staff_members=staff_members,
        days=DAYS,
        periods=PERIODS,
        substitutions= substitutions
    )
    
@app.route("/student-assignment", methods=["GET", "POST"])
def studentassignment():
   

    student_id = session.get('user_id')

    # Fetch all assignments and the assignment to edit (if any)
    assignments = db.fetchall(f"""
        SELECT a.id, subj.subject_name, s.name as student_name, a.description, a.due_date,sf.staff_name
        FROM tbl_assignment a 
        JOIN tbl_subject subj ON a.subject_id = subj.id
        JOIN tbl_student s ON a.student_id = s.login_id join tbl_staff sf on sf.login_id=a.staff_id where s.login_id={student_id}
    """)
    
    
    return render_template("student/assignments.html", assignments=assignments)


@app.route("/student-live-assignment", methods=["GET", "POST"])
def studentliveassignment():
    student_id = session.get('user_id')
   
    # Fetch all assignments and the assignment to edit (if any)
    assignments = db.fetchall(f"""
        SELECT a.id, subj.subject_name, s.name as student_name, a.description, a.due_date, sf.staff_name
        FROM tbl_assignment a 
        JOIN tbl_subject subj ON a.subject_id = subj.id
        JOIN tbl_student s ON a.student_id = s.login_id join tbl_staff sf on sf.login_id=a.staff_id where s.login_id={student_id} and a.due_date>now()
    """)
    
  
    return render_template("student/live_assignments.html", assignments=assignments)

@app.route("/student-expired-assignment", methods=["GET", "POST"])
def studentexpiredassignment():
    student_id = session.get('user_id')
   
    # Fetch all assignments and the assignment to edit (if any)
    assignments = db.fetchall(f"""
        SELECT a.id, subj.subject_name, s.name as student_name, a.description, a.due_date, sf.staff_name
        FROM tbl_assignment a 
        JOIN tbl_subject subj ON a.subject_id = subj.id
        JOIN tbl_student s ON a.student_id = s.login_id join tbl_staff sf on sf.login_id=a.staff_id where s.login_id={student_id} and a.due_date<=now()
    """)
    
  
    return render_template("student/expired_assignments.html", assignments=assignments)

from datetime import datetime, timedelta

@app.route("/substitutions", methods=["GET", "POST"])
def substitutions():
    student_id = session.get('user_id')
    
    # Fetch the course ID for the logged-in student
    query = f"SELECT course FROM tbl_student WHERE login_id={student_id}"
    result = db.fetchone(query)  # Fetch the result as a dictionary or tuple
    
    if result:
        course_id = result['course']  # Extract the 'course' value if result is a dictionary
        print(f"course: {course_id}")
    
        # Get the current date
        today = datetime.today()

        # Calculate the start (Monday) and end (Sunday) of the current week
        start_of_week = today - timedelta(days=today.weekday())  # Monday
        end_of_week = start_of_week + timedelta(days=6)  # Sunday

        # Modify the SQL query to fetch substitutions only for the current week
        select_query = f"""
            SELECT * FROM replace_staff 
            WHERE course_id = {course_id} 
            AND date >= '{start_of_week.strftime('%Y-%m-%d')}' 
            AND date <= '{end_of_week.strftime('%Y-%m-%d')}'
        """
        
        substitutions = db.fetchall(select_query)
        
        # Render the substitutions page
        return render_template("student/substitutions.html", substitutions=substitutions)
    
    else:
        # Handle case when course ID is not found
        return "Course ID not found", 404







# running application 
if __name__ == '__main__': 
    app.run(debug=True) 