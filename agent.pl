:- dynamic intent/1.
:- dynamic budget/1.
:- dynamic car/4.


price(CarId, Price) :-
    car(CarId, Price, _, _).

make(CarId, Make) :-
    car(CarId, _, Make, _).

model(CarId, Model) :-
    car(CarId, _, _, Model).

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