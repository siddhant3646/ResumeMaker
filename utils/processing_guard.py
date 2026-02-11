"""
Processing Guard - Prevents stuck processing states
Handles timeouts, debouncing, and proper cleanup
"""

import time
import streamlit as st
from datetime import datetime, timedelta
from typing import Optional


class ProcessingGuard:
    """
    Prevents stuck processing states with timeout and debouncing
    
    Features:
    - 5-minute timeout (configurable)
    - 500ms debounce between clicks
    - Automatic cleanup on timeout/error
    - Time remaining tracking
    """
    
    def __init__(self, timeout_seconds: int = 300):
        """
        Initialize processing guard
        
        Args:
            timeout_seconds: Maximum processing time before auto-reset (default: 300 = 5 min)
        """
        self.timeout = timeout_seconds
        self.last_click_key = "last_click_time"
        self.processing_key = "is_processing"
        self.start_time_key = "processing_start"
        self.user_id_key = "processing_user_id"
    
    def can_start_processing(self, user_id: Optional[str] = None) -> bool:
        """
        Check if processing can start
        
        Returns True if:
        - Not currently processing
        - Previous processing timed out
        - Debounce period passed (500ms)
        
        Args:
            user_id: Optional user ID to track who started processing
            
        Returns:
            bool: True if processing can start
        """
        # Check if currently processing
        is_processing = st.session_state.get(self.processing_key, False)
        
        if is_processing:
            start_time = st.session_state.get(self.start_time_key)
            if start_time:
                elapsed = time.time() - start_time
                if elapsed > self.timeout:
                    # Timed out, reset and allow restart
                    self.reset()
                    return self._check_debounce()
                else:
                    # Still processing within timeout
                    return False
            else:
                # No start time recorded, reset and allow
                self.reset()
                return self._check_debounce()
        
        # Not processing, check debounce
        return self._check_debounce()
    
    def _check_debounce(self) -> bool:
        """Check if debounce period has passed (500ms)"""
        last_click = st.session_state.get(self.last_click_key, 0)
        time_since_click = time.time() - last_click
        
        if time_since_click < 0.5:  # 500ms debounce
            return False
        
        return True
    
    def start(self, user_id: Optional[str] = None) -> None:
        """
        Mark processing as started
        
        Args:
            user_id: User who started processing (for tracking)
        """
        st.session_state[self.processing_key] = True
        st.session_state[self.start_time_key] = time.time()
        st.session_state[self.last_click_key] = time.time()
        if user_id:
            st.session_state[self.user_id_key] = user_id
    
    def reset(self) -> None:
        """Reset processing state"""
        keys_to_remove = [
            self.processing_key,
            self.start_time_key,
            self.last_click_key,
            self.user_id_key
        ]
        
        for key in keys_to_remove:
            if key in st.session_state:
                del st.session_state[key]
    
    def is_processing(self) -> bool:
        """Check if currently processing"""
        return st.session_state.get(self.processing_key, False)
    
    def get_time_remaining(self) -> int:
        """
        Get seconds remaining before timeout
        
        Returns:
            int: Seconds remaining (0 if not processing or timed out)
        """
        if not self.is_processing():
            return 0
        
        start_time = st.session_state.get(self.start_time_key)
        if not start_time:
            return 0
        
        elapsed = time.time() - start_time
        remaining = max(0, self.timeout - elapsed)
        return int(remaining)
    
    def get_elapsed_time(self) -> int:
        """
        Get seconds elapsed since processing started
        
        Returns:
            int: Seconds elapsed (0 if not processing)
        """
        if not self.is_processing():
            return 0
        
        start_time = st.session_state.get(self.start_time_key)
        if not start_time:
            return 0
        
        return int(time.time() - start_time)
    
    def get_processing_user(self) -> Optional[str]:
        """Get the user ID who started processing"""
        return st.session_state.get(self.user_id_key, None)
    
    def force_reset_if_stale(self) -> bool:
        """
        Force reset if processing has timed out
        
        Returns:
            bool: True if reset occurred
        """
        if not self.is_processing():
            return False
        
        start_time = st.session_state.get(self.start_time_key)
        if not start_time:
            self.reset()
            return True
        
        elapsed = time.time() - start_time
        if elapsed > self.timeout:
            self.reset()
            return True
        
        return False


class ProcessingStatus:
    """Helper class to display processing status"""
    
    @staticmethod
    def show_processing_warning(guard: ProcessingGuard) -> None:
        """Show warning if processing is ongoing"""
        if guard.is_processing():
            remaining = guard.get_time_remaining()
            elapsed = guard.get_elapsed_time()
            
            if remaining > 0:
                st.warning(
                    f"⏳ Resume generation in progress...\n\n"
                    f"Elapsed: {elapsed}s | Timeout in: {remaining}s"
                )
            else:
                st.error("⚠️ Previous session timed out. Please try again.")
                guard.reset()
    
    @staticmethod
    def show_debounce_message() -> None:
        """Show message when click is debounced"""
        st.info("⏳ Please wait a moment before clicking again...")
