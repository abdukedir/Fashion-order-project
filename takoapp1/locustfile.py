from locust import HttpUser, task, between
import json
import random

class OrderUser(HttpUser):
    wait_time = between(1, 3)

    # View products
    @task(1)
    def view_products(self):
        self.client.get("/products/")

    # Create order
    @task(3)
    def create_order(self):
        product_id = random.randint(1, 5)
        size = random.choice(["S", "M", "L", "XL"])
        color = random.choice(["Black", "White", "Red"])

        payload = {
            "username": f"user_{random.randint(1, 10000)}",
            "items": [
                {
                    "id": product_id,
                    "quantity": random.randint(1, 3),
                    "size": size,
                    "colors": [color]
                }
            ]
        }

        self.client.post(
            "/order/create/",
            data={
                "username": payload["username"],
                "items": json.dumps(payload["items"])
            },
            name="/order/create/"
        )

    # View today's confirmed orders report
    @task(1)
    def view_today_report(self):
        self.client.get("/reports/confirmed-orders/today/", name="/reports/confirmed-orders/today/")

    # View today's total quantity
    @task(1)
    def view_today_total(self):
        self.client.get("/reports/confirmed-orders/today/total/", name="/reports/confirmed-orders/today/total/")
