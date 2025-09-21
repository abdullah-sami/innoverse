# import time
# from django.db import connection, models
# from django.test import TestCase

# from .models import Participant, Team
# from participant.models import TeamParticipant


# class ParticipantTestCase(TestCase):
#     def setUp(self):
#         self.participant = Participant.objects.create(
#             f_name='John',
#             l_name='Doe',
#             email='john.doe@example.com',
#             phone='1234567890',
#             age=25,
#             institution='Example University',
#             institution_id='EX123',
#             address='123 Main St',
#             payment_verified=True
#         )

#     def test_model_str(self):
#         self.assertEqual(str(self.participant), 'John Doe')

#     def test_field_values(self):
#         self.assertEqual(self.participant.f_name, 'John')
#         self.assertEqual(self.participant.l_name, 'Doe')
#         self.assertEqual(self.participant.email, 'john.doe@example.com')
#         self.assertEqual(self.participant.phone, '1234567890')
#         self.assertEqual(self.participant.age, 25)
#         self.assertEqual(self.participant.institution, 'Example University')
#         self.assertEqual(self.participant.institution_id, 'EX123')
#         self.assertEqual(self.participant.address, '123 Main St')
#         self.assertEqual(self.participant.payment_verified, True)


# class TeamTestCase(TestCase):
#     def setUp(self):
#         self.team = Team.objects.create(
#             team_name='Team Alpha',
#             payment_verified=True
#         )

#     def test_model_str(self):
#         self.assertEqual(str(self.team), 'Team Alpha')

#     def test_field_values(self):
#         self.assertEqual(self.team.team_name, 'Team Alpha')
#         self.assertEqual(self.team.payment_verified, True)


# class TeamParticipantPerformanceTestCase(TestCase):
#     """
#     Performance test: Compare query execution with and without indexing
#     """
#     def setUp(self):
#         self.team = Team.objects.create(team_name="Benchmark Team")
#         # Insert bulk records to simulate large dataset
#         participants = [
#             TeamParticipant(
#                 f_name=f'User{i}',
#                 l_name='Benchmark',
#                 email=f'user{i}@example.com',
#                 phone=f'555000{i}',
#                 age=20 + (i % 10),
#                 institution='Perf College',
#                 institution_id=f'PC{i}',
#                 team=self.team,
#                 is_leader=(i == 0),
#             )
#             for i in range(5000)
#         ]
#         TeamParticipant.objects.bulk_create(participants)

#     def _time_query(self):
#         start = time.time()
#         list(TeamParticipant.objects.filter(email="user2500@example.com"))
#         return time.time() - start

#     def test_query_performance_with_and_without_index(self):
#         with connection.schema_editor() as editor:
#             # Drop index if it exists
#             try:
#                 editor.remove_index(
#                     TeamParticipant,
#                     models.Index(fields=["email"], name="team_part_email_idx"),
#                 )
#             except Exception:
#                 pass

#         # Query time without index
#         no_index_time = self._time_query()

#         with connection.schema_editor() as editor:
#             # Add index on email
#             editor.add_index(
#                 TeamParticipant,
#                 models.Index(fields=["email"], name="team_part_email_idx"),
#             )

#         # Query time with index
#         with_index_time = self._time_query()

#         print(f"\nQuery time without index: {no_index_time:.6f}s")
#         print(f"Query time with index:    {with_index_time:.6f}s")

#         # Assert that indexed query is faster (or at least not slower)
#         self.assertLessEqual(with_index_time, no_index_time)









from django.db import connection
from django.test import TestCase
from participant.models import TeamParticipant, Team
import time


class TeamParticipantPerformanceTestCase(TestCase):
    def setUp(self):
        self.team = Team.objects.create(team_name="Benchmark Team")

        participants = [
            TeamParticipant(
                f_name=f'User{i}',
                l_name='Benchmark',
                email=f'user{i}@example.com',
                phone=f'555000{i}',
                age=20 + (i % 10),
                institution='Perf College',
                institution_id=f'PC{i}',
                team=self.team,
                is_leader=(i == 0),
            )
            for i in range(5000)
        ]
        TeamParticipant.objects.bulk_create(participants)

    def _time_query(self):
        start = time.time()
        list(TeamParticipant.objects.filter(email="user2500@example.com"))
        return time.time() - start

    def test_query_performance_with_and_without_index(self):
        cursor = connection.cursor()

        # Drop index if exists
        cursor.execute("DROP INDEX IF EXISTS team_part_email_idx;")

        no_index_time = self._time_query()

        # Create index manually
        cursor.execute("CREATE INDEX team_part_email_idx ON participant_teamparticipant(email);")

        with_index_time = self._time_query()

        print(f"\nQuery time without index: {no_index_time:.6f}s")
        print(f"Query time with index:    {with_index_time:.6f}s")

        self.assertLessEqual(with_index_time, no_index_time)
