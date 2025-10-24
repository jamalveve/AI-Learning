import streamlit as st
import json
from datetime import datetime, timedelta
from pathlib import Path

# File path for persistence
TASKS_FILE = Path("tasks.json")

# Initialize session state
def init_session_state():
    """Initialize session state variables"""
    if 'tasks' not in st.session_state:
        st.session_state.tasks = load_tasks()
    if 'filter_priority' not in st.session_state:
        st.session_state.filter_priority = "All"
    if 'filter_date' not in st.session_state:
        st.session_state.filter_date = "All"

def load_tasks():
    """Load tasks from JSON file"""
    if TASKS_FILE.exists():
        try:
            with open(TASKS_FILE, 'r') as f:
                return json.load(f)
        except json.JSONDecodeError:
            return []
    return []

def save_tasks():
    """Save tasks to JSON file"""
    with open(TASKS_FILE, 'w') as f:
        json.dump(st.session_state.tasks, f, indent=2)

def add_task(name, due_date, priority):
    """Add a new task to the list"""
    task = {
        'id': len(st.session_state.tasks) + 1,
        'name': name,
        'due_date': due_date.strftime('%Y-%m-%d'),
        'priority': priority,
        'completed': False,
        'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }
    st.session_state.tasks.append(task)
    save_tasks()

def toggle_task_completion(task_id):
    """Mark a task as completed or uncompleted"""
    for task in st.session_state.tasks:
        if task['id'] == task_id:
            task['completed'] = not task['completed']
            save_tasks()
            break

def delete_task(task_id):
    """Delete a task from the list"""
    st.session_state.tasks = [t for t in st.session_state.tasks if t['id'] != task_id]
    save_tasks()

def filter_tasks(tasks, priority_filter, date_filter):
    """Filter tasks based on priority and date"""
    filtered = tasks.copy()
    
    # Filter by priority
    if priority_filter != "All":
        filtered = [t for t in filtered if t['priority'] == priority_filter]
    
    # Filter by date
    if date_filter != "All":
        today = datetime.now().date()
        for task in filtered[:]:
            task_date = datetime.strptime(task['due_date'], '%Y-%m-%d').date()
            
            if date_filter == "Today" and task_date != today:
                filtered.remove(task)
            elif date_filter == "This Week":
                week_end = today + timedelta(days=7)
                if task_date < today or task_date > week_end:
                    filtered.remove(task)
            elif date_filter == "Overdue" and task_date >= today:
                filtered.remove(task)
    
    return filtered

def get_priority_color(priority):
    """Return color code for priority level"""
    colors = {
        'High': '#ff4b4b',
        'Medium': '#ffa500',
        'Low': '#00cc00'
    }
    return colors.get(priority, '#808080')

def display_task_table(tasks, show_completed=False):
    """Display tasks in a formatted table"""
    if not tasks:
        st.info("No tasks to display." if not show_completed else "No completed tasks yet.")
        return
    
    for task in tasks:
        task_date = datetime.strptime(task['due_date'], '%Y-%m-%d').date()
        is_overdue = task_date < datetime.now().date() and not task['completed']
        
        col1, col2, col3, col4, col5 = st.columns([0.5, 3, 1.5, 1, 1])
        
        with col1:
            if st.checkbox("✓", value=task['completed'], key=f"check_{task['id']}", label_visibility="collapsed"):
                toggle_task_completion(task['id'])
                st.rerun()
        
        with col2:
            if task['completed']:
                st.markdown(f"~~{task['name']}~~")
            elif is_overdue:
                st.markdown(f"⚠️ **{task['name']}**")
            else:
                st.write(task['name'])
        
        with col3:
            date_str = task_date.strftime('%b %d, %Y')
            if is_overdue:
                st.markdown(f":{get_priority_color('High')}[{date_str}]")
            else:
                st.write(date_str)
        
        with col4:
            st.markdown(f":{get_priority_color(task['priority'])}[**{task['priority']}**]")
        
        with col5:
            if st.button("🗑️", key=f"del_{task['id']}", help="Delete task"):
                delete_task(task['id'])
                st.rerun()
        
        st.divider()

# Main app
def main():
    st.set_page_config(page_title="Task Tracker", page_icon="✅", layout="wide")
    init_session_state()
    
    st.title("📋 Task Tracker")
    st.markdown("---")
    
    # Add Task Section
    st.subheader("➕ Add New Task")
    col1, col2, col3, col4 = st.columns([3, 2, 2, 1])
    
    with col1:
        task_name = st.text_input("Task Name", placeholder="Enter task description...", label_visibility="collapsed")
    
    with col2:
        due_date = st.date_input("Due Date", value=datetime.now(), label_visibility="collapsed")
    
    with col3:
        priority = st.selectbox("Priority", ["High", "Medium", "Low"], label_visibility="collapsed")
    
    with col4:
        if st.button("Add Task", type="primary", use_container_width=True):
            if task_name.strip():
                add_task(task_name.strip(), due_date, priority)
                st.success("Task added!")
                st.rerun()
            else:
                st.error("Please enter a task name")
    
    st.markdown("---")
    
    # Filter Section
    st.subheader("🔍 Filter Tasks")
    col1, col2, col3 = st.columns([2, 2, 3])
    
    with col1:
        st.session_state.filter_priority = st.selectbox(
            "Filter by Priority",
            ["All", "High", "Medium", "Low"]
        )
    
    with col2:
        st.session_state.filter_date = st.selectbox(
            "Filter by Date",
            ["All", "Today", "This Week", "Overdue"]
        )
    
    with col3:
        task_count = len([t for t in st.session_state.tasks if not t['completed']])
        completed_count = len([t for t in st.session_state.tasks if t['completed']])
        st.metric("Active Tasks", task_count)
    
    st.markdown("---")
    
    # Active Tasks Section
    st.subheader("📝 Active Tasks")
    active_tasks = [t for t in st.session_state.tasks if not t['completed']]
    filtered_active = filter_tasks(active_tasks, st.session_state.filter_priority, st.session_state.filter_date)
    
    # Sort by due date and priority
    filtered_active.sort(key=lambda x: (
        datetime.strptime(x['due_date'], '%Y-%m-%d'),
        {'High': 0, 'Medium': 1, 'Low': 2}[x['priority']]
    ))
    
    display_task_table(filtered_active)
    
    st.markdown("---")
    
    # Completed Tasks Section
    if completed_count > 0:
        with st.expander(f"✅ Completed Tasks ({completed_count})", expanded=False):
            completed_tasks = [t for t in st.session_state.tasks if t['completed']]
            completed_tasks.sort(key=lambda x: datetime.strptime(x['due_date'], '%Y-%m-%d'), reverse=True)
            display_task_table(completed_tasks, show_completed=True)

if __name__ == "__main__":
    main()