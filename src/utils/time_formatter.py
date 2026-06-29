def format_hindenburg_time(total_milliseconds: float) -> str:
    """
    Converts float or int milliseconds to Hindenburg Narrator XML timing format.
    
    Rules:
    - Under 1 minute (60,000 ms): SS.mmm (e.g., 06.827 or 45.000). Do not include colons or minutes.
    - >= 1 minute but < 1 hour: MM:SS.mmm (e.g., 01:22.784 or 45:12.100).
    - >= 1 hour: H:MM:SS.mmm with no leading zero on the hour (e.g., 1:01:19.973).
    
    Args:
        total_milliseconds: Time in milliseconds.
        
    Returns:
        Hindenburg timing format string.
    """
    if total_milliseconds < 0:
        raise ValueError("Time milliseconds cannot be negative")
        
    # Round to nearest millisecond first
    rounded_ms = int(round(total_milliseconds))
    
    ms = rounded_ms % 1000
    total_seconds = rounded_ms // 1000
    
    if rounded_ms < 60000:
        return f"{total_seconds:02d}.{ms:03d}"
    elif rounded_ms < 3600000:
        minutes = total_seconds // 60
        seconds = total_seconds % 60
        return f"{minutes:02d}:{seconds:02d}.{ms:03d}"
    else:
        hours = total_seconds // 3600
        minutes = (total_seconds // 60) % 60
        seconds = total_seconds % 60
        return f"{hours}:{minutes:02d}:{seconds:02d}.{ms:03d}"

