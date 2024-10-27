import streamlit as st
import os
import json
import shutil
import logging
from datetime import datetime
from typing import Dict, Any, Optional
from reportlab.pdfgen import canvas
from reportlab.lib.units import mm
import pandas as pd
from streamlit_option_menu import option_menu
import time
import subprocess
from tkinter import filedialog
import tkinter as tk
import platform

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('order_management.log'),
        logging.StreamHandler()
    ]
)

class AppConfig:
    APP_NAME = "ExPresto"
    DEFAULT_BASE_PATH = "orders"
    ORDER_FILE = "orders.json"
    MAX_ORDER_ID_LENGTH = 50
    MAX_COMMENTS_LENGTH = 900
    STATUS_OPTIONS = ["In Progress", "Completed"]
    BASE_PATH = "orders"
    DONE_FOLDER = os.path.join(BASE_PATH, "_DONE")
    
    # Enhanced folder structure with descriptive names
    SUBFOLDER_STRUCTURE = {
        "01_FROM_CLIENT": ["PDF", "Podklady"],
        "02_RESOURCES": ["Fonts", "Photos"],
        "03_DESIGN": ["Work_Files", "Stock_assets"],
        "04_EXPORT": ["Print_Ready", "Preview"]
    }

def custom_css():
    """Enhanced Apple-inspired CSS styles"""
    st.markdown("""
        <style>
            /* Modern Apple-inspired dark theme */
            :root {
                --primary-color: #0A84FF;
                --secondary-color: #30D158;
                --background-dark: #1C1C1E;
                --card-background: #2C2C2E;
                --text-primary: #FFFFFF;
                --text-secondary: #98989D;
                --border-color: #3A3A3C;
                --hover-color: #3A3A3C;
            }
            
            /* Base styles */
            .stApp, .main, .css-1d391kg, [data-testid="stVerticalBlock"] {
                background-color: var(--background-dark) !important;
                color: var(--text-primary);
            }
            
            /* Enhanced card design */
            .order-card {
                background-color: var(--card-background);
                border-radius: 12px;
                padding: 20px;
                margin: 15px 0;
                border: 1px solid var(--border-color);
                transition: all 0.3s ease;
                box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
            }
            
            .order-card:hover {
                transform: translateY(-2px);
                box-shadow: 0 6px 8px rgba(0, 0, 0, 0.2);
            }
            
            /* Modern button styles */
            .stButton button {
                background-color: var(--primary-color) !important;
                color: white !important;
                border: none !important;
                border-radius: 8px !important;
                padding: 8px 16px !important;
                font-weight: 500 !important;
                transition: all 0.3s ease !important;
            }
            
            .stButton button:hover {
                opacity: 0.9;
                transform: translateY(-1px);
            }
            
            /* Input field styling */
            .stTextInput input, .stNumberInput input, .stTextArea textarea {
                background-color: var(--card-background) !important;
                color: var(--text-primary) !important;
                border: 1px solid var(--border-color) !important;
                border-radius: 8px !important;
                padding: 8px 12px !important;
            }
            
            /* Success message animation */
            .success-message {
                background-color: var(--secondary-color);
                color: white;
                padding: 12px;
                border-radius: 8px;
                margin: 10px 0;
                animation: slideIn 0.5s ease-out;
            }
            
            @keyframes slideIn {
                from {
                    transform: translateY(-20px);
                    opacity: 0;
                }
                to {
                    transform: translateY(0);
                    opacity: 1;
                }
            }
            
            /* Navigation menu styling */
            .nav-link {
                background-color: var(--card-background) !important;
                border-radius: 8px !important;
                margin: 0 5px !important;
            }
            
            .nav-link-selected {
                background-color: var(--primary-color) !important;
                color: white !important;
            }
            
            /* Stats card styling */
            .stats-card {
                background-color: var(--card-background);
                border-radius: 12px;
                padding: 20px;
                text-align: center;
                border: 1px solid var(--border-color);
            }
            
            .stats-number {
                font-size: 2em;
                font-weight: bold;
                color: var(--primary-color);
            }
        </style>
    """, unsafe_allow_html=True)


def select_base_path():
    """Open file dialog to select base path"""
    try:
        root = tk.Tk()
        root.withdraw()  # Hide the main window
        
        # Set dialog title based on OS
        if platform.system() == 'Darwin':  # macOS
            root.wm_attributes('-topmost', 1)  # Ensure dialog appears on top
        
        directory = filedialog.askdirectory(
            title="Select Base Directory",
            initialdir=os.path.expanduser("~")  # Start from user's home directory
        )
        
        if directory:
            st.session_state.base_path = directory
            st.session_state.orders = load_orders()  # Reload orders with new path
            save_app_config()  # Save the selected path
            show_success_message(f"Base path updated to: {directory}")
            return True
    except Exception as e:
        logging.error(f"Error selecting base path: {str(e)}")
        st.error("Failed to select directory")
    return False
def save_app_config():
    """Save application configuration"""
    try:
        config = {
            "base_path": st.session_state.base_path
        }
        with open("app_config.json", "w") as f:
            json.dump(config, f)
    except Exception as e:
        logging.error(f"Error saving app config: {str(e)}")

def load_app_config():
    """Load application configuration"""
    try:
        if os.path.exists("app_config.json"):
            with open("app_config.json", "r") as f:
                config = json.load(f)
                return config.get("base_path", AppConfig.DEFAULT_BASE_PATH)
    except Exception as e:
        logging.error(f"Error loading app config: {str(e)}")
    return AppConfig.DEFAULT_BASE_PATH
def load_orders() -> Dict[str, Any]:
    try:
        orders_file = os.path.join(AppConfig.BASE_PATH, AppConfig.ORDER_FILE)
        if os.path.exists(orders_file):
            with open(orders_file, 'r') as f:
                return json.load(f)
        return {}
    except Exception as e:
        logging.error(f"Error loading orders: {str(e)}")
        return {}


def init_session_state():
    """Initialize session state with enhanced error handling"""
    try:
        # Initialize session state
        if 'orders' not in st.session_state:
            st.session_state.orders = load_orders()
        if 'orders_list' not in st.session_state:
            st.session_state.orders_list = list(st.session_state.orders.values()) 
        if 'base_path' not in st.session_state:
            st.session_state.base_path = load_app_config()
        if 'success_message' not in st.session_state:
            st.session_state.success_message = None
        if 'success_timestamp' not in st.session_state:
            st.session_state.success_timestamp = None
        if 'confirm_clear' not in st.session_state:
            st.session_state.confirm_clear = False      
    except Exception as e:
        logging.error(f"Error initializing session state: {str(e)}")
        st.error("Failed to initialize application state")

def clear_all_orders():
    """Clear all orders from the list but keep them on disk"""
    try:
        if hasattr(st.session_state, 'orders_list') and st.session_state.orders_list:
            # Clear orders list from session state
            st.session_state.orders_list = []
            
            # Update the orders dictionary
            st.session_state.orders = {}
            
            show_success_message("All orders have been cleared from the list")
            time.sleep(0.5)  # Brief pause for visual feedback
            return True
            
    except Exception as e:
        logging.error(f"Error clearing orders: {str(e)}")
        st.error("Failed to clear orders")
        return False
def browse_path():
    """Open file dialog to select base path"""
    try:
        root = tk.Tk()
        root.withdraw()  # Hide the main window
        root.wm_attributes('-topmost', 1)  # Keep dialog on top
        
        # Open directory dialog
        directory = filedialog.askdirectory(
            title="Select Orders Base Directory",
            initialdir=os.path.expanduser("~")  # Start from user's home directory
        )
        
        if directory:
            # Update session state and paths
            st.session_state.base_path = directory
            AppConfig.BASE_PATH = directory
            AppConfig.DONE_FOLDER = os.path.join(directory, "_DONE")
            
            # Create base directory if it doesn't exist
            if not os.path.exists(directory):
                os.makedirs(directory)
            
            # Create DONE folder if it doesn't exist
            if not os.path.exists(AppConfig.DONE_FOLDER):
                os.makedirs(AppConfig.DONE_FOLDER)
            
            # Save the new path to config
            config = {"base_path": directory}
            with open("app_config.json", "w") as f:
                json.dump(config, f)
            
            # Reload orders from new location
            st.session_state.orders = load_orders()
            
            show_success_message(f"Base path updated to: {directory}")
            # Removed st.experimental_rerun() as it's not a valid Streamlit function
            return True
            
    except Exception as e:
        logging.error(f"Error in browse path: {str(e)}")
        st.error("Failed to select directory")
    return False
def render_dashboard():
    """Enhanced dashboard with modern stats display"""
    try:
        # Display current base path and browse button
        col1, col2 = st.columns([3, 1])
        with col1:
            st.text(f"Current Base Path: {st.session_state.base_path}")
        with col2:
            if st.button("Browse Path", key="browse_path"):
                select_base_path()

        # Enhanced statistics display
        st.subheader("Order Statistics")
        orders = st.session_state.orders
        total_orders = len(orders)
        completed_orders = sum(1 for order in orders.values() if order["status"] == "Completed")
        in_progress_orders = total_orders - completed_orders
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown("""
                <div class="stats-card">
                    <div class="stats-number">{}</div>
                    <div>Total Orders</div>
                </div>
            """.format(total_orders), unsafe_allow_html=True)
            
        with col2:
            st.markdown("""
                <div class="stats-card">
                    <div class="stats-number" style="color: #FF9F0A;">{}</div>
                    <div>In Progress</div>
                </div>
            """.format(in_progress_orders), unsafe_allow_html=True)
            
        with col3:
            st.markdown("""
                <div class="stats-card">
                    <div class="stats-number" style="color: #30D158;">{}</div>
                    <div>Completed</div>
                </div>
            """.format(completed_orders), unsafe_allow_html=True)

        # Recent activity
        if orders:
            st.subheader("Recent Activity")
            recent_orders = dict(sorted(
                orders.items(),
                key=lambda x: datetime.strptime(x[1]['created_date'], "%Y-%m-%d %H:%M:%S"),
                reverse=True
            )[:5])
            
            for order_id, order in recent_orders.items():
                st.markdown(f"""
                    <div class="order-card">
                        <h4>{order_id}</h4>
                        <p>Status: {order['status']}</p>
                        <p>Created: {order['created_date']}</p>
                    </div>
                """, unsafe_allow_html=True)

    except Exception as e:
        logging.error(f"Error rendering dashboard: {str(e)}")
        st.error("Failed to load dashboard")

def show_success_message(message: str):
    st.session_state.success_message = message
    st.session_state.success_timestamp = datetime.now()

def open_file_explorer(path: str):
    try:
        if os.path.exists(path):
            if os.name == 'nt':  # Windows
                subprocess.Popen(f'explorer "{path}"')
            elif os.name == 'posix':  # macOS and Linux
                if os.path.exists('/usr/bin/xdg-open'):  # Linux
                    subprocess.Popen(['xdg-open', path])
                else:  # macOS
                    subprocess.Popen(['open', path])
    except Exception as e:
        logging.error(f"Error opening file explorer: {str(e)}")
        st.error("Failed to open file explorer")


def save_orders(orders: Dict[str, Any]) -> bool:
    try:
        if not os.path.exists(AppConfig.BASE_PATH):
            os.makedirs(AppConfig.BASE_PATH)
        
        orders_file = os.path.join(AppConfig.BASE_PATH, AppConfig.ORDER_FILE)
        with open(orders_file, 'w') as f:
            json.dump(orders, f, indent=4)
        return True
    except Exception as e:
        logging.error(f"Error saving orders: {str(e)}")
        return False

def create_folder_structure(order_id: str) -> Optional[str]:
    try:
        base_folder = os.path.join(AppConfig.BASE_PATH, order_id)
        if os.path.exists(base_folder):
            st.error(f"Folder already exists for order {order_id}")
            return None

        os.makedirs(base_folder)
        
        for main_folder, sub_folders in AppConfig.SUBFOLDER_STRUCTURE.items():
            main_path = os.path.join(base_folder, main_folder)
            os.makedirs(main_path)
            
            for sub_folder in sub_folders:
                os.makedirs(os.path.join(main_path, sub_folder))
        
        open_file_explorer(base_folder)
        return base_folder
    except Exception as e:
        logging.error(f"Error creating folder structure: {str(e)}")
        st.error(f"Failed to create folder structure: {str(e)}")
        return None

def generate_job_sheet_with_safezone(order_data: Dict[str, Any], output_path: str, 
                                   width: float, height: float, safe_zone: float) -> bool:
    """Generate PDF job sheet with safe zone visualization"""
    try:
        # Convert mm to points (1 mm = 2.83465 points)
        width_pt = width * mm
        height_pt = height * mm
        safe_zone_pt = safe_zone * mm

        # Create PDF with specified dimensions
        c = canvas.Canvas(output_path, pagesize=(width_pt, height_pt))
        
        # Draw outer border
        c.rect(0, 0, width_pt, height_pt)
        
        # Draw safe zone
        c.setStrokeColorRGB(1, 0, 0)  # Red color for safe zone
        c.rect(safe_zone_pt, safe_zone_pt, 
               width_pt - (2 * safe_zone_pt), 
               height_pt - (2 * safe_zone_pt))
        
        # Add order details
        c.setFont("Helvetica-Bold", 12)
        text_x = safe_zone_pt + 5*mm
        text_y = height_pt - (safe_zone_pt + 15*mm)
        
        # Order information
        c.drawString(text_x, text_y, f"Order ID: {order_data['order_id']}")
        c.drawString(text_x, text_y - 15*mm, f"Created: {order_data['created_date']}")
        c.drawString(text_x, text_y - 30*mm, f"Dimensions: {width}mm x {height}mm")
        c.drawString(text_x, text_y - 45*mm, f"Safe Zone: {safe_zone}mm")
        
        if order_data.get('comments'):
            c.drawString(text_x, text_y - 60*mm, "Comments:")
            c.setFont("Helvetica", 10)
            comments = order_data['comments']
            # Wrap comments if too long
            wrapped_text = [comments[i:i+50] for i in range(0, len(comments), 50)]
            for i, line in enumerate(wrapped_text):
                c.drawString(text_x, text_y - (75 + i*15)*mm, line)

        c.save()
        return True
    except Exception as e:
        logging.error(f"Error generating job sheet: {str(e)}")
        return False
def move_to_completed(order_id: str) -> bool:
    """Move order to completed folder with visual feedback"""
    try:
        if order_id not in st.session_state.orders:
            st.error("Order not found")
            return False

        order = st.session_state.orders[order_id]
        source_path = order["folder_path"]
        
        if not os.path.exists(source_path):
            st.error("Source folder not found")
            return False

        # Create _DONE folder if it doesn't exist
        if not os.path.exists(AppConfig.DONE_FOLDER):
            os.makedirs(AppConfig.DONE_FOLDER)

        # Move folder to _DONE
        with st.spinner("Moving files to completed..."):
            dest_path = os.path.join(AppConfig.DONE_FOLDER, os.path.basename(source_path))
            shutil.move(source_path, dest_path)

            # Update order status and path
            order["status"] = "Completed"
            order["folder_path"] = dest_path
            save_orders(st.session_state.orders)

        return True

    except Exception as e:
        logging.error(f"Error moving order to completed: {str(e)}")
        st.error(f"Failed to move order: {str(e)}")
        return False

def move_to_in_progress(order_id: str) -> bool:
    """Move order back to in-progress folder with visual feedback"""
    try:
        if order_id not in st.session_state.orders:
            st.error("Order not found")
            return False

        order = st.session_state.orders[order_id]
        source_path = order["folder_path"]
        
        if not os.path.exists(source_path):
            st.error("Source folder not found")
            return False

        # Move folder from _DONE back to main directory
        with st.spinner("Moving files back to in-progress..."):
            dest_path = os.path.join(AppConfig.BASE_PATH, os.path.basename(source_path))
            shutil.move(source_path, dest_path)

            # Update order status and path
            order["status"] = "In Progress"
            order["folder_path"] = dest_path
            save_orders(st.session_state.orders)

        return True

    except Exception as e:
        logging.error(f"Error moving order to in-progress: {str(e)}")
        st.error(f"Failed to move order: {str(e)}")
        return False

def handle_order_status_change(order_id: str, to_completed: bool):
    """Handle order status change with appropriate folder movement"""
    try:
        if to_completed:
            if move_to_completed(order_id):
                show_success_message(f"Order {order_id} marked as completed")
        else:
            if move_to_in_progress(order_id):
                show_success_message(f"Order {order_id} moved back to in-progress")
                
    except Exception as e:
        logging.error(f"Error handling status change: {str(e)}")
        st.error(f"Failed to change order status: {str(e)}")


def display_order_stats():
    """Display order statistics"""
    try:
        orders = st.session_state.orders
        
        total_orders = len(orders)
        completed_orders = sum(1 for order in orders.values() if order["status"] == "Completed")
        in_progress_orders = total_orders - completed_orders
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Total Orders", total_orders)
        with col2:
            st.metric("In Progress", in_progress_orders)
        with col3:
            st.metric("Completed", completed_orders)
            
    except Exception as e:
        logging.error(f"Error displaying stats: {str(e)}")
        st.error("Failed to display statistics")

def validate_dimensions(width: float, height: float, safe_zone: float) -> bool:
    """Validate input dimensions"""
    if width <= 0 or height <= 0:
        st.error("Width and height must be positive numbers")
        return False
    if safe_zone <= 0:
        st.error("Safe zone must be positive")
        return False
    if safe_zone * 2 >= min(width, height):
        st.error("Safe zone too large for given dimensions")
        return False
    return True
def render_new_order_form():
    """Render the new order creation form with dimensions input"""
    try:
        with st.form("new_order_form"):
            order_id = st.text_input(
                "Order ID",
                max_chars=AppConfig.MAX_ORDER_ID_LENGTH,
                help="Enter a unique identifier for the order"
            ).strip()

            # Dimensions input
            col1, col2, col3 = st.columns(3)
            with col1:
                width = st.number_input("Width (mm)", min_value=1.0, value=100.0, step=1.0)
            with col2:
                height = st.number_input("Height (mm)", min_value=1.0, value=100.0, step=1.0)
            with col3:
                safe_zone = st.number_input("Safe Zone (mm)", min_value=1.0, value=3.0, step=0.5)

            comments = st.text_area(
                "Comments",
                max_chars=AppConfig.MAX_COMMENTS_LENGTH,
                help="Add any additional notes or comments"
            )

            submitted = st.form_submit_button("Create Order")

            if submitted:
                if not order_id:
                    st.error("Order ID is required")
                    return

                if order_id in st.session_state.orders:
                    st.error("Order ID already exists")
                    return

                if not validate_dimensions(width, height, safe_zone):
                    return

                # Create folder structure
                folder_path = create_folder_structure(order_id)
                if not folder_path:
                    return

                # Create order data
                order_data = {
                    "order_id": order_id,
                    "comments": comments,
                    "status": "In Progress",
                    "folder_path": folder_path,
                    "created_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "width": width,
                    "height": height,
                    "safe_zone": safe_zone
                }

                # Generate job sheet with safe zone
                job_sheet_path = os.path.join(folder_path, "02_REFERENCES", f"{order_id}_job_sheet.pdf")
                if not generate_job_sheet_with_safezone(order_data, job_sheet_path, width, height, safe_zone):
                    st.error("Failed to generate job sheet")
                    return

                # Save order
                st.session_state.orders[order_id] = order_data
                st.session_state.orders_list = list(st.session_state.orders.values())
                if save_orders(st.session_state.orders):
                    show_success_message(f"Order {order_id} created successfully")
                    time.sleep(0.5)
                    st.rerun()
                else:
                    st.error("Failed to save order")

    except Exception as e:
        logging.error(f"Error in new order form: {str(e)}")
        st.error("Failed to create order")

def render_order_management():
    try:
        st.header("Order Management")
        
        # Check if orders exist
        if not hasattr(st.session_state, 'orders') or not st.session_state.orders:
            st.info("No orders available")
            return

        # Add Clear All button with confirmation
        if 'show_confirm' not in st.session_state:
            st.session_state.show_confirm = False

        if st.button("Clear All Orders", key="clear_all", help="Remove all orders from the system"):
            st.session_state.show_confirm = True

        if st.session_state.show_confirm:
            st.warning("Are you sure you want to delete all orders? This action cannot be undone.")
            col1, col2 = st.columns(2)
            with col1:
                if st.button("Yes, Clear All", key="confirm_clear"):
                    clear_all_orders()
                    st.session_state.show_confirm = False
                    st.experimental_rerun()
            with col2:
                if st.button("Cancel", key="cancel_clear"):
                    st.session_state.show_confirm = False
                    st.experimental_rerun()

        # Filter orders by status
        status_filter = st.multiselect(
            "Filter by Status",
            AppConfig.STATUS_OPTIONS,
            default=AppConfig.STATUS_OPTIONS,
            key="status_filter"
        )

        # Filter and display orders
        filtered_orders = {
            k: v for k, v in st.session_state.orders.items()
            if v["status"] in status_filter
        }

        # Display orders
        if filtered_orders:
            for order_id, order in filtered_orders.items():
                # Add default values for width, height, and safe_zone if they don't exist
                width = order.get('width', 'N/A')
                height = order.get('height', 'N/A')
                safe_zone = order.get('safe_zone', 'N/A')
                
                with st.container():
                    st.markdown(f"""
                        <div class="order-card">
                            <div style="display: flex; justify-content: space-between; align-items: center;">
                                <div>
                                    <h3 style="margin: 0;">Order: {order_id}</h3>
                                    <p style="margin: 5px 0;">Status: {order['status']}</p>
                                    <p style="margin: 5px 0;">Created: {order.get('created_date', 'N/A')}</p>
                                    <p style="margin: 5px 0;">Dimensions: {width}mm x {height}mm (Safe Zone: {safe_zone}mm)</p>
                                    {f'<p style="margin: 5px 0;">Comments: {order["comments"]}</p>' if order.get('comments') else ''}
                                </div>
                            </div>
                        </div>
                    """, unsafe_allow_html=True)
                    
                    col1, col2 = st.columns([0.5, 0.5])
                    
                    with col1:
                        is_completed = order["status"] == "Completed"
                        st.checkbox(
                            "Completed",
                            key=f"status_{order_id}",
                            value=is_completed,
                            on_change=handle_order_status_change,
                            args=(order_id, not is_completed),
                        )
                    
                    with col2:
                        if st.button("📁 Open Folder", key=f"open_{order_id}"):
                            open_file_explorer(order["folder_path"])
        else:
            st.info("No orders match the selected filters")

    except Exception as e:
        logging.error(f"Error in order management: {str(e)}")
        st.error("Failed to manage orders")

def render_dashboard():
    """Enhanced dashboard rendering"""
    st.header("Dashboard")
    
    # Display stats with animations
    display_order_stats()
    
    # Settings section
    st.header("Settings")
    with st.container():
        st.markdown("""
            <div class="settings-container">
                <h3>Base Path Configuration</h3>
            </div>
        """, unsafe_allow_html=True)
        
        col1, col2 = st.columns([0.8, 0.2])
        with col1:
            st.text_input(
                label="Current Base Path",
                value=st.session_state.base_path,
                key="base_path_display",
                disabled=True,
                label_visibility="collapsed"  # This will hide the label
            )
        with col2:
            if st.button("Browse", key="browse_path", use_container_width=True):
                browse_path()



def main():
    """Enhanced main application function"""
    try:
        st.set_page_config(
            page_title=AppConfig.APP_NAME,
            page_icon="🎨",
            layout="wide",
            initial_sidebar_state="collapsed",
            menu_items={
                'About': f"{AppConfig.APP_NAME} v2.1\nDesigned with precision"
            }
        )

        custom_css()
        init_session_state()

        # Modern header with logo
        st.markdown(f"""
            <div style="display: flex; align-items: center; margin-bottom: 20px;">
                <h1 style="margin: 0;">🎨 {AppConfig.APP_NAME}</h1>
            </div>
        """, unsafe_allow_html=True)
        
        # Enhanced navigation
        selected = option_menu(
            menu_title=None,
            options=["Dashboard", "New Order", "Manage Orders"],
            icons=["speedometer2", "plus-circle", "list-check"],
            menu_icon="cast",
            default_index=0,
            orientation="horizontal",
            styles={
                "container": {"padding": "0!important", "background-color": "transparent"},
                "icon": {"color": "white", "font-size": "25px"},
                "nav-link": {
                    "font-size": "16px",
                    "text-align": "center",
                    "margin": "0px",
                    "--hover-color": "#3A3A3C",
                    "font-weight": "500",
                },
                "nav-link-selected": {"background-color": "#0A84FF"},
            }
        )

        # Display success message with animation
        if st.session_state.success_message:
            st.markdown(f"""
                <div class="success-message">
                    ✨ {st.session_state.success_message}
                </div>
            """, unsafe_allow_html=True)
            
            if st.session_state.success_timestamp:
                if (datetime.now() - st.session_state.success_timestamp).seconds > 3:
                    st.session_state.success_message = None
                    st.session_state.success_timestamp = None

        # Render selected page
        if selected == "Dashboard":
            render_dashboard()
        elif selected == "New Order":
            st.header("Create New Order")
            render_new_order_form()
        elif selected == "Manage Orders":
            st.header("Manage Orders")
            render_order_management()

    except Exception as e:
        logging.error(f"Application error: {str(e)}")
        st.error("An unexpected error occurred. Please try again.")

if __name__ == "__main__":
    main()