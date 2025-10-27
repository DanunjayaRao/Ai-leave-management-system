from database import LeaveDatabase

class AuthSystem:
    def __init__(self, database):
        self.db = database
        self.current_user = None
        self.user_role = None
        self.default_password = "leave"
    
    def authenticate(self, user_id, password):
        """Authenticate user"""
        if not user_id or not password:
            return False, "Please enter both User ID and Password"
        
        if password != self.default_password:
            return False, "Invalid password"
        
        try:
            user_id_int = int(user_id)
            
            # Check if employee (1000-1010)
            if 1000 <= user_id_int <= 1010:
                self.current_user = user_id
                self.user_role = "employee"
                return True, f"Employee login successful! Welcome User {user_id}"
            
            # Check if admin
            if user_id_int in [5000, 8001, 6099]:
                self.current_user = user_id
                self.user_role = "admin"
                return True, f"Admin login successful! Welcome Admin {user_id}"
            
            return False, "User ID not found. Valid IDs: 1000-1010 (Employees), 5000/8001/6099 (Admins)"
        except ValueError:
            return False, "Invalid User ID format"
        except Exception as e:
            return False, f"Authentication error: {str(e)}"
    
    def logout(self):
        """Logout current user"""
        self.current_user = None
        self.user_role = None
    
    def get_current_user(self):
        return self.current_user, self.user_role
    
    def is_logged_in(self):
        return self.current_user is not None