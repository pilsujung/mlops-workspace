import time


class CircuitBreaker:

    CLOSED = "CLOSED"
    OPEN = "OPEN"
    HALF_OPEN = "HALF_OPEN"

    def __init__(self, failure_threshold=2, recovery_timeout=10):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout

        self.state = CircuitBreaker.CLOSED
        self.failure_count = 0
        self.last_failure_time = None

    def call(self, request_model, fallback, *args, **kwargs):

        # OPEN 상태
        if self.state == CircuitBreaker.OPEN:
            if time.time() - self.last_failure_time > self.recovery_timeout:
                self.state = CircuitBreaker.HALF_OPEN
                print("CircuitBreaker → HALF_OPEN")
                print("time.time() - self.last_failure_time =", time.time() - self.last_failure_time)

            else:
                print("CircuitBreaker OPEN → fallback")
                return fallback()

        try:
            result = request_model(*args, **kwargs)

            # HALF_OPEN 성공 → CLOSED
            if self.state == CircuitBreaker.HALF_OPEN:
                print("CircuitBreaker HALF_OPEN success → CLOSED")
                self.state = CircuitBreaker.CLOSED
                self.failure_count = 0

            return result

        except Exception as e:

            self.failure_count += 1
            self.last_failure_time = time.time()

            print("Service call failed:", e)

            if self.failure_count >= self.failure_threshold:
                self.state = CircuitBreaker.OPEN
                print("CircuitBreaker → OPEN")

            return fallback()
