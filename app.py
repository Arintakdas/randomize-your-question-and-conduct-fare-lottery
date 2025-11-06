import streamlit as st
import pandas as pd
import random
import json
import os
import re

DATA_FILE = "DSA_PCA_2.xlsx"
HISTORY_FILE = "assignment_history.json"
ROLL_NO_COLUMN = "Roll No."
PROBLEMS_COLUMN = "Please choose any 13 Probem Statements from the following"
MAX_ASSIGNMENTS_PER_QUESTION = 4

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
        st.error("Error: Missing 'openpyxl' library. Please install it (`pip install openpyxl`) to read Excel files.")
        return None
    except Exception as e:
        st.error(f"An error occurred while loading the data: {e}")
        return None

def load_history(file_path):
    if os.path.exists(file_path):
        try:
            with open(file_path, 'r') as f:
                data = json.load(f)
                if "assignments" not in data:
                    data["assignments"] = {}
                if "counts" not in data:
                    data["counts"] = {}
                return data
        except json.JSONDecodeError:
            st.warning("History file is corrupted. Starting with a new history.")
            return {"assignments": {}, "counts": {}}
        except Exception as e:
            st.error(f"Error loading history: {e}")
            return {"assignments": {}, "counts": {}}
    else:
        return {"assignments": {}, "counts": {}}

def save_history(file_path, history_data):
    try:
        with open(file_path, 'w') as f:
            json.dump(history_data, f, indent=4)
    except Exception as e:
        st.error(f"CRITICAL: Failed to save assignment history: {e}")

def parse_problems_string(problem_str):
    if not isinstance(problem_str, str):
        return []
    problems = [p.strip() for p in problem_str.split(',')]
    return [p for p in problems if p]

@st.cache_data
def get_student_problems(df, roll_no):
    student_row = df[df[ROLL_NO_COLUMN] == roll_no]
    if not student_row.empty:
        problem_str = student_row.iloc[0][PROBLEMS_COLUMN]
        return parse_problems_string(problem_str)
    else:
        return None

@st.cache_data
def get_unassigned_pool(df, full_problem_list):
    all_chosen_problems = set()
    for problem_str in df[PROBLEMS_COLUMN].dropna():
        problems = parse_problems_string(problem_str)
        all_chosen_problems.update(problems)
    
    full_problem_set = set(full_problem_list)
    unassigned_set = full_problem_set - all_chosen_problems
    
    return list(unassigned_set)

def select_question(problem_list, history_counts):
    if not problem_list:
        return None, "Error: The problem pool to select from is empty."

    available_problems = [
        q for q in problem_list 
        if history_counts.get(q, 0) < MAX_ASSIGNMENTS_PER_QUESTION
    ]

    if not available_problems:
        return None, "All problems in your pool have already been assigned the maximum number of times (4)."

    chosen_question = random.choice(available_problems)
    return chosen_question, "Success!"

def main():
    st.set_page_config(page_title="DSA Problem Lottery", layout="wide", initial_sidebar_state="expanded")
    st.title("DSA Problem Statement Lottery System ")

    df = load_data(DATA_FILE)
    history_data = load_history(HISTORY_FILE)

    if df is None:
        st.error("Application cannot start without the data file. Please check the file name and location.")
        return

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

                if roll_no in history_data["assignments"]:
                    st.warning(f"**Roll number {roll_no} has already been assigned a question.**")
                    assigned_question = history_data["assignments"][roll_no]
                    st.info(f"Your previously assigned question is:")
                    st.markdown(f"## **{assigned_question}**")
                    st.balloons()
                
                else:
                    problem_pool = []
                    pool_source = ""

                    student_problems = get_student_problems(df, roll_no)
                    
                    if student_problems:
                        problem_pool = student_problems
                        pool_source = f"your 13 chosen problems (Roll No. {roll_no} found)."
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
                        st.write(f"Selecting from a pool of {len(problem_pool)} questions from {pool_source}")
                        
                        chosen_question, message = select_question(problem_pool, history_data["counts"])
                        
                        if chosen_question:
                            st.success(f"**Congrats! Your assigned problem is:**")
                            st.markdown(f"## **{chosen_question}**")
                            st.balloons()
                            
                            history_data["assignments"][roll_no] = chosen_question
                            current_count = history_data["counts"].get(chosen_question, 0)
                            history_data["counts"][chosen_question] = current_count + 1
                            
                            save_history(HISTORY_FILE, history_data)
                            st.caption("Your assignment has been saved.")
                        
                        else:
                            st.error(f"**Could not assign a question.**")
                            st.error(f"Reason: {message}")
                    else:
                        st.error(f"Cannot assign a problem. The pool of problems (from {pool_source}) is empty.")

    elif page == "Assignment History":
        st.header("Assignment History")

        if not history_data["assignments"]:
            st.info("No assignments have been made yet.")
            return

        st.subheader("Assignments per Student")
        try:
            assignments_df = pd.DataFrame(
                history_data["assignments"].items(), 
                columns=["Roll Number", "Assigned Question"]
            )
            st.dataframe(assignments_df, use_container_width=True)
        except Exception as e:
            st.error(f"Could not display student assignments: {e}")

        st.subheader("Assignment Counts per Question")
        try:
            if history_data["counts"]:
                counts_df = pd.DataFrame(
                    history_data["counts"].items(), 
                    columns=["Question", "Times Assigned"]
                )
                counts_df = counts_df.sort_values(by="Times Assigned", ascending=False)
                st.dataframe(counts_df, use_container_width=True)
            else:
                st.info("No questions have been assigned yet.")
        except Exception as e:
            st.error(f"Could not display question counts: {e}")


if __name__ == "__main__":
    main()
