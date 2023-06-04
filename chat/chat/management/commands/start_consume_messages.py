import multiprocessing
from django.core.management.base import BaseCommand
from chat.tasks import base_consumer


class Command(BaseCommand):
    help = 'Consume Kafka messages'

    def handle(self, *args, **options):
        processes = []

        # Launch multiple consumers in separate processes
        process1 = multiprocessing.Process(target=base_consumer)
        # Add other consumer processes as needed

        processes.append(process1)

        # Start all the consumer processes
        for process in processes:
            process.start()

        # Wait for all the consumer processes to finish
        for process in processes:
            process.join()

        self.stdout.write(self.style.SUCCESS(
            "Message consumption via kafka broker started successfully for all tasks"))
