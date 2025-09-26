% The goal is to have a customer schedule a test drive
% for a car within their budget.

magic(15573).

% intent can be 'buy' or 'sell'
:- dynamic intent/1.
% budget is a number representing the customer's budget
:- dynamic budget/1.
% car(CarId, Price, Make, Model)
:- dynamic car/4.
% customer_available(Year, Month, Day, Hour)
:- dynamic customer_available/4.
% shop_available(Year, Month, Day, Hour)

shop_available(Year, Month, Day, Hour) :-
    % Shop is open from 9am to 6pm
    Hour >= 9,
    Hour =< 18,
    % Shop is open Monday to Friday
    date_time_stamp(date(Year, Month, Day, Hour, 0, 0, 0, -, -), Timestamp),
    stamp_date_time(Timestamp, DateTime, local),
    DateTime = date(_, _, _, _, _, _, WeekDay, _, _),
    WeekDay >= 1,
    WeekDay =< 5.


price(CarId, Price) :-
    car(CarId, Price, _, _).

make(CarId, Make) :-
    car(CarId, _, Make, _).

model(CarId, Model) :-
    car(CarId, _, _, Model).

action(schedule_test_drive(CarId, Year, Month, Day, Hour)) :-
    intent(buy),
    budget(Budget),
    car(CarId, Price, _, _),
    Price =< Budget,
    customer_available(Year, Month, Day, Hour),
    shop_available(Year, Month, Day, Hour).

action(ask_for_availability) :-
    intent(buy),
    budget(Budget),
    car(_, Price, _, _),
    Price =< Budget,
    \+ customer_available(_, _, _, _).

action(ask_intent) :-
    \+ intent(_).

action(ask_budget) :-
    intent(buy),
    \+ budget(_).

action(tell_we_only_buy) :-
    intent(sell).

action(fetch_inventory) :-
    intent(buy),
    budget(_),
    \+ car(_, _, _, _).

action(recommend(CarId, Price, Make, Model)) :-
    intent(buy),
    budget(Budget),
    car(CarId, Price, Make, Model),
    Price =< Budget.