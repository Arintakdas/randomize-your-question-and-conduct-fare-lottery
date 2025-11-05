import streamlit as st
import pandas as pd
import random
import gspread
from google.oauth2.service_account import Credentials
import os
from collections import defaultdict

DATA_FILE = "DSA PCA 2 Lottery Validation form (Responses).xlsx"
ROLL_NO_COLUMN = "Roll No."
PROBLEMS_COLUMN = "Please choose any 13 Probem Statements from the following"
MAX_ASSIGNMENTS_PER_QUESTION = 4

GSHEET_NAME = "LotteryAppHistory" 
WORKSHEET_NAME = "Assignments"
EXCLUSION_WORKSHEET_NAME = "Exclusions"

FULL_PROBLEM_LIST = [
    "Fibonacci Number",
    "Amstrong Prime and Largest among three",
    "Array creation display and element Search",
    "Permutation of Strings",
    "Calculate length of string reverse the string and copy it to another string without using any library functions",
    "Graphics (Draw Rectangle Circle and Triangle and perform rotation scaling and translation operation)",
    "Digital and Analogue Clock",
    "File operations: Reading Writing a 1. String 2. Binary and closing a file",
    "Menu driven file operation to store n number of student name and marks and perform 1. Append new records 2. Delete record 3. Update record 4. Display Records operations",
    "Menu driven file operation to perform 1. Print file content 2. Copy file content from one file to another 3. Merge 2 file contents 4. Delete a specific file",
    "PGM Image to negative image",
    "Menu driven file operation (.CSV file) to store n number of student name and marks and perform 1. Insert new records 2. Delete record 3. Update record 4. Search Records operations",
    "Array : Creation Display Linear Search Binary Search Insertion Deletion by 1. Given position and 2. given item",
    "Array: Creation Display Selection Sort",
    "Array: Creation Display Bubble Sort Modified Bubble Sort",
    "Array: Creation Display Insertion sort",
    "Array: Creation Display Merge Sort",
    "Dynamic Linked List: Creation Display Display using recursion Searching Insertion Deletion Reverse print Reverse linked list",
    "Dynamic Double Linked List: Creation Display Display using recursion Searching Insertion Deletion Reverse print Reverse linked list",
    "Circular Linked List: Creation Display Insertion Deletion Searching",
    "Stack: Push Pop Display",
    "Infix to Postfix expression",
    "Implement postfix evaluation algorithm",
    "Static Queue: Insertion Deletion Display",
    "Dynamic Queue: Insertion Deletion Display",
    "Circular Queue: Insertion Deletion Display",
    "Tower of Hanoi",
    "BST (Binary Search Tree) : Creation In order Traversal Post Order Traversal Pre order traversal Searching Insertion Deletion",
    "Heap Tree (Max Heap) using array : Creation In order pre order and post order traversal Sorting Display original and sorted list"
]

@st.cache_data
def load_data(file_path):
    try:
        df = pd.read_excel(file_path)
        if ROLL_NO_COLUMN in df.columns:
            df[ROLL_NO_COLUMN] = df[ROLL_NO_COLUMN].astype(str).str.split('.').str[0]
        else:
            st.error(f"Error: Column '{ROLL_NO_COLUMN}' not found in the file.")
            return None
        if PROBLEMS_COLUMN not in df.columns:
            st.error(f"Error: Column '{PROBLEMS_COLUMN}' not found in the file.")
            return None
        return df
    except FileNotFoundError:
        st.error(f"Error: Data file '{file_path}' not found.")
        return None
    except ImportError:
        st.error("Error: Missing 'openpyxl' library.")
        return None
    except Exception as e:
        st.error(f"An error occurred while loading the data: {e}")
        return None

@st.cache_resource
def connect_to_gsheet():
    try:
        creds_dict = st.secrets["gcp_service_account"]
        creds = Credentials.from_service_account_info(creds_dict)
        scoped_creds = creds.with_scopes([
            "https.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive",
        ])
        gc = gspread.authorize(scoped_creds)
        return gc
    except Exception as e:
        st.error(f"Error connecting to Google Sheets: {e}")
        return None

def get_worksheet(gc, sheet_name, worksheet_name):
    if gc is None:
        return None
    try:
        sh = gc.open(sheet_name)
        ws = sh.worksheet(worksheet_name)
        return ws
    except gspread.exceptions.SpreadsheetNotFound:
        st.error(f"Error: Google Sheet named '{sheet_name}' not found.")
        return None
    except gspread.exceptions.WorksheetNotFound:
        st.error(f"Error: Worksheet tab named '{worksheet_name}' not found.")
        return None
    except Exception as e:
        st.error(f"Error opening worksheet {worksheet_name}: {e}")
        return None

def load_history(ws):
    if ws is None:
        return {"assignments": {}, "counts": {}}
    try:
        records = ws.get_all_records()
        assignments = {str(row['Roll Number']): row['Assigned Question'] for row in records}
        counts = pd.Series(list(assignments.values())).value_counts().to_dict()
        return {"assignments": assignments, "counts": counts}
    except Exception as e:
        st.error(f"Error loading history from {ws.title}: {e}")
        return {"assignments": {}, "counts": {}}

def load_exclusions(ws_exclude):
    if ws_exclude is None:
        return {}
    try:
        records = ws_exclude.get_all_records()
        exclusions = defaultdict(list)
        for row in records:
            exclusions[str(row['Roll Number'])].append(row['Excluded Question'])
        return exclusions
    except Exception as e:
        st.error(f"Error loading exclusions from {ws_exclude.title}: {e}")
        return {}

def save_history(ws, roll_no, question):
    if ws is None:
        st.error("Cannot save history. No connection to Google Sheet.")
        return
    try:
        ws.append_row([roll_no, question])
    except Exception as e:
        st.error(f"CRITICAL: Failed to save assignment to Google Sheet: {e}")

def delete_history(ws, ws_exclude, roll_no, question):
    if ws is None or ws_exclude is None:
        st.error("Cannot delete. No connection to Google Sheet.")
        return False
    try:
        ws_exclude.append_row([roll_no, question])
        
        cell = ws.find(roll_no)
        if cell:
            ws.delete_rows(cell.row)
        
        return True
    except Exception as e:
        st.error(f"CRITICAL: Failed to archive assignment: {e}")
        return False

def parse_problems_string(problem_str):
    if not isinstance(problem_str, str):
        return []
    problems = [p.strip() for p in problem_str.split(',')]
    return [p for p in problems if p]

@st.cache_data
def get_student_problems(_df, roll_no):
    student_row = _df[_df[ROLL_NO_COLUMN] == roll_no]
    if not student_row.empty:
        problem_str = student_row.iloc[0][PROBLEMS_COLUMN]
        return parse_problems_string(problem_str)
    else:
        return None

@st.cache_data
def get_unassigned_pool(_df, full_problem_list):
    all_chosen_problems = set()
    for problem_str in _df[PROBLEMS_COLUMN].dropna():
        problems = parse_problems_string(problem_str)
        all_chosen_problems.update(problems)
    
    full_problem_set = set(full_problem_list)
    unassigned_set = full_problem_set - all_chosen_problems
    return list(unassigned_set)

def select_question(problem_list, history_counts, personal_exclusions):
    if not problem_list:
        return None, "Error: The problem pool to select from is empty."
    
    available_problems = [
        q for q in problem_list 
        if history_counts.get(q, 0) < MAX_ASSIGNMENTS_PER_QUESTION
    ]
    
    if not available_problems:
        return None, "All problems in your pool have already been assigned the maximum number of times (4)."
    
    final_pool = [
        q for q in available_problems
        if q not in personal_exclusions
    ]
    
    if not final_pool:
        return None, "All available problems in your pool have been assigned to you in the past. Cannot assign a new one."
    
    chosen_question = random.choice(final_pool)
    return chosen_question, "Success!"

def main():
    st.set_page_config(page_title="DSA Problem Lottery", layout="wide", initial_sidebar_state="expanded")
    st.title("👨‍💻 DSA Problem Statement Lottery System 🎲")

    df = load_data(DATA_FILE)
    if df is None:
        st.error("Application cannot start without the data file. Please check the file name and location.")
        return

    gc = connect_to_gsheet()
    ws = get_worksheet(gc, GSHEET_NAME, WORKSHEET_NAME)
    ws_exclude = get_worksheet(gc, GSHEET_NAME, EXCLUSION_WORKSHEET_NAME)
    
    page = st.sidebar.radio("Navigation", ["Lottery", "Assignment History"])
    st.sidebar.markdown("---")
    st.sidebar.info(f"Loaded {len(df)} student responses.")
    st.sidebar.caption("@2025 vediccoder A.das")

    if page == "Lottery":
        st.header("Get Your Problem")
        
        with st.form("lottery_form"):
            roll_no_input = st.text_input("Enter your 11-digit Roll Number:", value="110001240", max_chars=11)
            submit_button = st.form_submit_button("Get My Question", type="primary")

        if submit_button:
            if not (roll_no_input.isdigit() and len(roll_no_input) == 11):
                st.error("Please enter a valid 11-digit Roll Number.")
            else:
                roll_no = roll_no_input.strip()
                st.markdown("---")
                
                history_data = load_history(ws)
                
                if roll_no in history_data["assignments"]:
                    st.info("You already had an assignment. We are re-rolling for you...")
                    old_question = history_data["assignments"][roll_no]
                    
                    delete_history(ws, ws_exclude, roll_no, old_question)
                    
                    st.warning(f"Your previous question ('{old_question}') has been un-assigned and added to your exclusion list.")
                    
                    history_data = load_history(ws)
                
                problem_pool = []
                pool_source = ""
                student_problems = get_student_problems(df, roll_no)
                
                if student_problems:
                    problem_pool = student_problems
                    pool_source = "your 13 chosen problems"
                    st.success(f"🎉 Congrats! Roll Number **{roll_no}** found. Selecting from your 13 chosen problems...")
                
                else:
                    st.error(f"This roll no. ({roll_no}) not register in google form")
                    problem_pool = get_unassigned_pool(df, FULL_PROBLEM_LIST)
                    
                    if problem_pool:
                        st.info("Assigning a question from the general unassigned problem pool...")
                        pool_source = "the general unassigned pool."
                    else:
                        st.warning("The 'general unassigned problem pool' is empty.")
                        st.info("Assigning a question from the complete problem list instead...")
                        problem_pool = FULL_PROBLEM_LIST
                        pool_source = "the complete problem list (fallback)."
                        
                    if not problem_pool:
                        st.error("Error: The complete problem list is empty. Cannot assign a question.")
                        return

                if problem_pool:
                    exclusions_data = load_exclusions(ws_exclude)
                    my_exclusions = exclusions_data.get(roll_no, [])
                    
                    chosen_question, message = select_question(
                        problem_pool, 
                        history_data["counts"], 
                        my_exclusions
                    )
                    
                    if chosen_question:
                        st.success(f"**Congrats! Your new assigned problem is:**")
                        st.markdown(f"## **{chosen_question}**")
                        st.balloons()
                        
                        save_history(ws, roll_no, chosen_question)
                        st.caption("Your assignment has been saved.")
                    
                    else:
                        st.error(f"**Could not assign a question.** Reason: {message}")
                else:
                    st.error(f"Cannot assign a problem. The pool of problems (from {pool_source}) is empty.")

    elif page == "Assignment History":
        st.header("Assignment History")
        
        history_data = load_history(ws)
        exclusions_data = load_exclusions(ws_exclude)

        if not history_data["assignments"]:
            st.info("No active assignments have been made yet.")
        else:
            st.subheader("Active Assignments per Student")
            assignments_df = pd.DataFrame(
                history_data["assignments"].items(), 
                columns=["Roll Number", "Assigned Question"]
            )
            st.dataframe(assignments_df, use_container_width=True)

            st.subheader("Active Assignment Counts per Question")
            if history_data["counts"]:
                counts_df = pd.DataFrame(
                    history_data["counts"].items(), 
                    columns=["Question", "Times Assigned"]
                )
                counts_df = counts_df.sort_values(by="Times Assigned", ascending=False)
                st.dataframe(counts_df, use_container_width=True)
            
            st.markdown("---")
            st.subheader("Un-assign a Student (Admin)")
            st.caption("This will move the student's assignment to the 'Exclusions' list.")
            
            if not history_data["assignments"]:
                st.warning("No students to un-assign.")
            else:
                roll_to_delete = st.selectbox(
                    "Choose Roll Number to un-assign:",
                    options=sorted(history_data["assignments"].keys())
                )
                
                if st.button(f"Un-assign {roll_to_delete}", type="primary"):
                    if roll_to_delete in history_data["assignments"]:
                        question_to_delete = history_data["assignments"][roll_to_delete]
                        
                        success = delete_history(ws, ws_exclude, roll_to_delete, question_to_delete)
                        if success:
                            st.success(f"Un-assigned {roll_to_delete} and logged to exclusions.")
                            st.experimental_rerun()
                    else:
                        st.error(f"{roll_to_delete} not found in history.")

if __name__ == "__main__":
    main()
