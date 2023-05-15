import csv
import random
from datetime import datetime, timedelta
from faker import Faker

fake = Faker()

# Define the number of customers, workers, and tasks to generate
NUM_CUSTOMERS = 10
NUM_WORKERS = 5
TASKS_PER_CUSTOMER = 50

# Define the range of hourly rates for workers
MIN_HOURLY_RATE = 20
MAX_HOURLY_RATE = 50

# Define the range of start and end times for tasks
MIN_START_TIME = datetime(2023, 1, 1, 0, 0, 0)
MAX_START_TIME = datetime(2023, 12, 31, 23, 59, 59)
TASK_DURATION = timedelta(hours=2)

# Generate the customer data
customer_data = []
for i in range(NUM_CUSTOMERS):
    username = fake.user_name()
    email = fake.email()
    phone_number = fake.phone_number()
    location = fake.address()
    profile_picture = fake.image_url()
    customer_data.append([username, email, phone_number, location, profile_picture])

# Generate the worker data
worker_data = []
for i in range(NUM_WORKERS):
    username = fake.user_name()
    email = fake.email()
    phone_number = fake.phone_number()
    location = fake.address()
    skills = fake.words(nb=3)
    hourly_rate = random.uniform(MIN_HOURLY_RATE, MAX_HOURLY_RATE)
    is_available = fake.boolean()
    profile_picture = fake.image_url()
    worker_data.append(
        [
            username,
            email,
            phone_number,
            location,
            skills,
            hourly_rate,
            is_available,
            profile_picture,
        ]
    )

# Generate the task data
task_data = []
for i in range(NUM_CUSTOMERS):
    customer_username = customer_data[i][0]
    for j in range(TASKS_PER_CUSTOMER):
        worker_username = worker_data[j % NUM_WORKERS][0]
        title = fake.sentence(nb_words=4)
        description = fake.paragraph()
        start_time = fake.date_time_between_dates(MIN_START_TIME, MAX_START_TIME)
        end_time = start_time + TASK_DURATION
        location = fake.address()
        status = random.choice(["requested", "in-progress", "completed", "rejected"])
        rating = random.randint(0, 5) if status == "completed" else None
        review = fake.paragraph() if status == "completed" else None
        hourly_rate = worker_data[j % NUM_WORKERS][5]
        total_cost = (end_time - start_time).total_seconds() / 3600 * hourly_rate
        task_data.append(
            [
                customer_username,
                worker_username,
                title,
                description,
                start_time,
                end_time,
                location,
                status,
                rating,
                review,
                hourly_rate,
                total_cost,
            ]
        )

# Save the data to a CSV file
with open("householddata.csv", "w", newline="") as file:
    writer = csv.writer(file)
    writer.writerow(
        [
            "Customer Username",
            "Worker Username",
            "Title",
            "Description",
            "Start Time",
            "End Time",
            "Location",
            "Status",
            "Rating",
            "Review",
            "Hourly Rate",
            "Total Cost",
        ]
    )
    for row in task_data:
        writer.writerow(row)
