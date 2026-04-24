import csv
import os
import time

class Guardrail:

    def __init__(self, dataset_path="iris.csv", ood_log="OOD.csv"):
        """
        Guardrail 초기화

        dataset_path : 학습 데이터 파일 (iris.csv)
        ood_log      : OOD 입력을 기록할 파일
        """

        self.dataset_path = dataset_path
        self.ood_log = ood_log

        # 각 feature의 최소/최대 값을 저장할 변수
        self.min_vals = [float("inf")] * 4  # 4개의 float value 담을 공간 생성
        self.max_vals = [float("-inf")] * 4

        # 요청 시간 기록 (rate limiting용)
        self.request_times = []

        # 데이터셋을 읽어서 feature 범위를 계산
        self._load_dataset()


    def _load_dataset(self):
        """
        iris.csv를 읽어서
        각 feature의 최소값과 최대값을 계산한다.
        """

        with open(self.dataset_path, "r") as f:
            reader = csv.reader(f)

            for row in reader:

                # 앞의 4개 값만 사용 (label 제외)
                values = list(map(float, row[:4]))

                for i in range(4):
                    self.min_vals[i] = min(self.min_vals[i], values[i])
                    self.max_vals[i] = max(self.max_vals[i], values[i])


    def is_ood(self, values):
        """
        입력값이 OOD(out-of-distribution)인지 검사한다.

        기준:
        학습 데이터에서 관측된 feature 범위를 벗어나면 OOD로 판단
        """

        for i in range(4):

            # feature 범위를 벗어나면 OOD
            if values[i] < self.min_vals[i] or values[i] > self.max_vals[i]:
                return True

        return False


    def log_ood(self, values):
        """
        OOD 입력을 OOD.csv 파일에 기록한다.
        """

        # 파일이 존재하지 않으면 header를 먼저 기록
        write_header = not os.path.exists(self.ood_log)

        with open(self.ood_log, "a", newline="") as f:
            writer = csv.writer(f)

            if write_header:
                writer.writerow([
                    "sepal_length",
                    "sepal_width",
                    "petal_length",
                    "petal_width"
                ])

            # OOD 입력 기록
            writer.writerow(values)

    # Rate Limiting
    def allow_request(self):
        """
        10초 내 3회 초과 요청 차단 (Rate limiting)
        """

        now = time.time()

        # 10초 이전 요청 제거
        self.request_times = [
            t for t in self.request_times if now - t < 10
        ]

        if len(self.request_times) >= 3:  # 최근 10초 내 요청이 3회 이상이면 차단
            return False

        self.request_times.append(now)  # 현재 요청 시간 추가

        return True
