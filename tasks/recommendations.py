from typing import List, Dict
from math import sqrt
from django.db.models import Avg, Count, Q
from tasks.models import Task
from users.models import Worker


def pearson_correlation_coefficient(worker_id, available_workers, n: int = 5):
    worker_ratings = {}  # A dictionary to store the ratings of the specified worker
    worker_tasks = Task.objects.filter(worker__id=worker_id, status="completed")
    for task in worker_tasks:
        worker_ratings[task.customer.id] = task.rating

    # A dictionary to store the Pearson correlation coefficient of each worker with the specified worker
    similarities = {}

    for worker in available_workers:
        if worker.id != worker_id:
            worker_tasks = Task.objects.filter(worker__id=worker.id, status="completed")
            ratings = {}
            for task in worker_tasks:
                ratings[task.customer.id] = task.rating

            # Calculate the Pearson correlation coefficient between the specified worker and the current worker
            numerator = 0
            denominator1 = 0
            denominator2 = 0
            for customer_id, rating in worker_ratings.items():
                if customer_id in ratings:
                    numerator += (rating - sum(ratings.values()) / len(ratings)) * (
                        ratings[customer_id] - sum(ratings.values()) / len(ratings)
                    )
                    denominator1 += (rating - sum(ratings.values()) / len(ratings)) ** 2
                    denominator2 += (
                        ratings[customer_id] - sum(ratings.values()) / len(ratings)
                    ) ** 2

            if denominator1 == 0 or denominator2 == 0:
                similarity = 0
            else:
                similarity = numerator / sqrt(denominator1 * denominator2)

            similarities[worker.id] = similarity

    # Sort the workers by their similarity to the specified worker
    similar_workers = sorted(similarities.items(), key=lambda x: x[1], reverse=True)

    # Get the top N similar workers
    top_similar_workers = []
    for worker_id, similarity in similar_workers[:n]:
        worker = Worker.objects.get(id=worker_id)
        top_similar_workers.append(worker)

    return top_similar_workers