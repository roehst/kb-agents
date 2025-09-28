"""
Built-in predicates for MiniProlog.
This module implements common Prolog built-in predicates that are not part of the core logic.
"""

from datetime import datetime, timezone
from typing import List

from kb_agents.miniprolog.syntax import Predicate, NumericConst
from kb_agents.miniprolog.subst import Subst
from kb_agents.miniprolog.unify import unify


def is_builtin(predicate: Predicate) -> bool:
    """Check if a predicate is a built-in predicate."""
    builtin_names = {
        "date_time_stamp",
        "stamp_date_time",
        "get_time",
        "format_time",
        "current_time",
        "weekday",
    }
    return predicate.name in builtin_names


def evaluate_builtin(predicate: Predicate, subst: Subst) -> List[Subst]:
    """Evaluate a built-in predicate and return possible substitutions."""
    if predicate.name == "date_time_stamp":
        return _date_time_stamp(predicate, subst)
    elif predicate.name == "stamp_date_time":
        return _stamp_date_time(predicate, subst)
    elif predicate.name == "get_time":
        return _get_time(predicate, subst)
    elif predicate.name == "current_time":
        return _current_time(predicate, subst)
    elif predicate.name == "weekday":
        return _weekday(predicate, subst)
    else:
        return []


def _date_time_stamp(predicate: Predicate, subst: Subst) -> List[Subst]:
    """
    date_time_stamp(+DateTime, -TimeStamp)
    Convert a date/time structure to a timestamp.
    DateTime is date(Year, Month, Day, Hour, Min, Sec, _, _, _)
    """
    if len(predicate.args) != 2:
        return []
    
    date_term = subst.apply(predicate.args[0])
    timestamp_term = subst.apply(predicate.args[1])
    
    # Check if date_term is a compound term date(Year, Month, Day, Hour, Min, Sec, _, _, _)
    if isinstance(date_term, Predicate) and date_term.name == "date" and len(date_term.args) >= 6:
        try:
            # Extract the date components
            year_term = subst.apply(date_term.args[0])
            month_term = subst.apply(date_term.args[1])
            day_term = subst.apply(date_term.args[2])
            hour_term = subst.apply(date_term.args[3])
            min_term = subst.apply(date_term.args[4])
            sec_term = subst.apply(date_term.args[5])
            
            # Convert to numeric values
            if all(isinstance(t, NumericConst) for t in [year_term, month_term, day_term, hour_term, min_term, sec_term]):
                year = int(year_term.numeric_value())  # type: ignore
                month = int(month_term.numeric_value())  # type: ignore
                day = int(day_term.numeric_value())  # type: ignore
                hour = int(hour_term.numeric_value())  # type: ignore
                minute = int(min_term.numeric_value())  # type: ignore
                second = int(sec_term.numeric_value())  # type: ignore
                
                # Create datetime and convert to timestamp
                dt = datetime(year, month, day, hour, minute, second, tzinfo=timezone.utc)
                timestamp = int(dt.timestamp())
                
                # Try to unify with the timestamp term
                timestamp_const = NumericConst(name=str(timestamp))
                new_subst = unify(timestamp_term, timestamp_const, subst)
                if new_subst is not None:
                    return [new_subst]
        except (ValueError, OverflowError):
            pass
    
    return []


def _stamp_date_time(predicate: Predicate, subst: Subst) -> List[Subst]:
    """
    stamp_date_time(+TimeStamp, -DateTime, +TimeZone)
    Convert a timestamp to a date/time structure.
    DateTime is date(Year, Month, Day, Hour, Min, Sec, WeekDay, YearDay, DST)
    """
    if len(predicate.args) != 3:
        return []
    
    timestamp_term = subst.apply(predicate.args[0])
    datetime_term = subst.apply(predicate.args[1])
    # timezone_term = subst.apply(predicate.args[2])  # Not used for now
    
    if isinstance(timestamp_term, NumericConst):
        try:
            timestamp = timestamp_term.numeric_value()
            dt = datetime.fromtimestamp(timestamp, tz=timezone.utc)
            
            # Calculate weekday (Monday=1, Sunday=7 as in ISO 8601)
            weekday = dt.isoweekday()
            
            # Calculate year day (1-366)
            year_day = dt.timetuple().tm_yday
            
            # DST is 0 for UTC
            dst = 0
            
            # Create the date structure
            date_structure = Predicate(
                name="date",
                args=[
                    NumericConst(name=str(dt.year)),
                    NumericConst(name=str(dt.month)),
                    NumericConst(name=str(dt.day)),
                    NumericConst(name=str(dt.hour)),
                    NumericConst(name=str(dt.minute)),
                    NumericConst(name=str(dt.second)),
                    NumericConst(name=str(weekday)),
                    NumericConst(name=str(year_day)),
                    NumericConst(name=str(dst)),
                ]
            )
            
            # Try to unify with the datetime term
            new_subst = unify(datetime_term, date_structure, subst)
            if new_subst is not None:
                return [new_subst]
        except (ValueError, OverflowError):
            pass
    
    return []


def _get_time(predicate: Predicate, subst: Subst) -> List[Subst]:
    """
    get_time(-TimeStamp)
    Get the current timestamp.
    """
    if len(predicate.args) != 1:
        return []
    
    timestamp_term = subst.apply(predicate.args[0])
    current_timestamp = int(datetime.now(timezone.utc).timestamp())
    timestamp_const = NumericConst(name=str(current_timestamp))
    
    new_subst = unify(timestamp_term, timestamp_const, subst)
    if new_subst is not None:
        return [new_subst]
    
    return []


def _current_time(predicate: Predicate, subst: Subst) -> List[Subst]:
    """
    current_time(-TimeStamp)
    Alias for get_time/1.
    """
    return _get_time(predicate, subst)


def _weekday(predicate: Predicate, subst: Subst) -> List[Subst]:
    """
    weekday(+Year, +Month, +Day, -WeekDay)
    Calculate the weekday for a given date.
    WeekDay: 1=Monday, 2=Tuesday, ..., 7=Sunday (ISO 8601 standard)
    """
    if len(predicate.args) != 4:
        return []
    
    year_term = subst.apply(predicate.args[0])
    month_term = subst.apply(predicate.args[1])
    day_term = subst.apply(predicate.args[2])
    weekday_term = subst.apply(predicate.args[3])
    
    # All input terms must be numeric constants
    if not all(isinstance(t, NumericConst) for t in [year_term, month_term, day_term]):
        return []
    
    try:
        year = int(year_term.numeric_value())  # type: ignore
        month = int(month_term.numeric_value())  # type: ignore
        day = int(day_term.numeric_value())  # type: ignore
        
        # Create datetime and get ISO weekday (1=Monday, 7=Sunday)
        dt = datetime(year, month, day)
        weekday = dt.isoweekday()
        
        # Try to unify with the weekday term
        weekday_const = NumericConst(name=str(weekday))
        new_subst = unify(weekday_term, weekday_const, subst)
        if new_subst is not None:
            return [new_subst]
    except (ValueError, OverflowError):
        pass
    
    return []


__all__ = ["is_builtin", "evaluate_builtin"]