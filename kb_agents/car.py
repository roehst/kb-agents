from pydantic import BaseModel


class Car(BaseModel):
    identifier: str
    make: str
    model: str
    price: float
    color: str
    year: int


example_data = [
    Car(
        identifier="toy-cam-1",
        make="Toyota",
        model="Camry",
        price=24000,
        color="Blue",
        year=2020,
    ),
    Car(
        identifier="hon-acc-2",
        make="Honda",
        model="Accord",
        price=26000,
        color="Black",
        year=2021,
    ),
    Car(
        identifier="for-mus-3",
        make="Ford",
        model="Mustang",
        price=30000,
        color="Red",
        year=2022,
    ),
    Car(
        identifier="che-mal-4",
        make="Chevrolet",
        model="Malibu",
        price=22000,
        color="White",
        year=2019,
    ),
    Car(
        identifier="nis-alt-5",
        make="Nissan",
        model="Altima",
        price=25000,
        color="Gray",
        year=2020,
    ),
    Car(
        identifier="tes-mod3-6",
        make="Tesla",
        model="Model 3",
        price=35000,
        color="Silver",
        year=2021,
    ),
    Car(
        identifier="bmw-320i-7",
        make="BMW",
        model="320i",
        price=40000,
        color="Blue",
        year=2022,
    ),
    Car(
        identifier="aud-a4-8",
        make="Audi",
        model="A4",
        price=42000,
        color="Black",
        year=2021,
    ),
    Car(
        identifier="mer-c300-9",
        make="Mercedes-Benz",
        model="C300",
        price=45000,
        color="White",
        year=2022,
    ),
    Car(
        identifier="vol-s60-10",
        make="Volvo",
        model="S60",
        price=38000,
        color="Red",
        year=2020,
    ),
    # Italian cars
    Car(
        identifier="fer-488-11",
        make="Ferrari",
        model="488",
        price=250000,
        color="Red",
        year=2020,
    ),
    Car(
        identifier="lam-hur-12",
        make="Lamborghini",
        model="Huracan",
        price=300000,
        color="Yellow",
        year=2021,
    ),
    Car(
        identifier="mas-ghibli-13",
        make="Maserati",
        model="Ghibli",
        price=80000,
        color="Blue",
        year=2022,
    ),
    # Cheap cars
    Car(
        identifier="kia-rio-14",
        make="Kia",
        model="Rio",
        price=15000,
        color="Green",
        year=2019,
    ),
    Car(
        identifier="hyu-elantra-15",
        make="Hyundai",
        model="Elantra",
        price=16000,
        color="White",
        year=2020,
    ),
    Car(
        identifier="for-fiesta-16",
        make="Ford",
        model="Fiesta",
        price=14000,
        color="Red",
        year=2018,
    ),
    Car(
        identifier="niss-versa-17",
        make="Nissan",
        model="Versa",
        price=13000,
        color="Blue",
        year=2019,
    ),
    Car(
        identifier="che-spark-18",
        make="Chevrolet",
        model="Spark",
        price=12000,
        color="Yellow",
        year=2018,
    ),
    # Old cars
    Car(
        identifier="toy-corolla-19",
        make="Toyota",
        model="Corolla",
        price=10000,
        color="Silver",
        year=2015,
    ),
    Car(
        identifier="hon-civic-20",
        make="Honda",
        model="Civic",
        price=11000,
        color="Black",
        year=2016,
    ),
    # Collectibles
    Car(
        identifier="for-mustang-66",
        make="Ford",
        model="Mustang",
        price=55000,
        color="Red",
        year=1966,
    ),
    Car(
        identifier="che-corvette-59",
        make="Chevrolet",
        model="Corvette",
        price=60000,
        color="Blue",
        year=1959,
    ),
]

__all__ = [
    "Car",
    "example_data",
]
