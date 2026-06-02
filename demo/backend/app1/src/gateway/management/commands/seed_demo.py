from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
import zipfile
import io
import os

User = get_user_model()


class Command(BaseCommand):
    help = "Seed the database with demo users and sample test files"

    def add_arguments(self, parser):
        parser.add_argument(
            "--clear",
            action="store_true",
            help="Delete existing demo users before seeding",
        )

    def handle(self, *args, **options):
        self.stdout.write("Seeding demo data...")

        demo_users = [
            {
                "username": "demo_user1",
                "email": "demo1@superapp.local",
                "password": "DemoPass123!",
                "first_name": "Tanaka",
                "last_name": "Taro",
            },
            {
                "username": "demo_user2",
                "email": "demo2@superapp.local",
                "password": "DemoPass456!",
                "first_name": "Suzuki",
                "last_name": "Hanako",
            },
            {
                "username": "demo_user3",
                "email": "demo3@superapp.local",
                "password": "DemoPass789!",
                "first_name": "Yamada",
                "last_name": "Ichiro",
            },
        ]

        if options["clear"]:
            for user in demo_users:
                User.objects.filter(username=user["username"]).delete()
            self.stdout.write(self.style.WARNING("Cleared existing demo users"))

        created = []
        for data in demo_users:
            user, made = User.objects.get_or_create(
                username=data["username"],
                defaults=data,
            )
            if made:
                user.set_password(data["password"])
                user.save()
                created.append(data["username"])
            else:
                user.set_password(data["password"])
                user.save()
                self.stdout.write(
                    self.style.WARNING(f"Updated password for {data['username']}")
                )

        self.stdout.write(
            self.style.SUCCESS(f"Seeded {len(created)} demo users: {', '.join(created)}")
        )

        sample_zip_path = os.path.join(os.getcwd(), "sample_demo.zip")
        if not os.path.exists(sample_zip_path):
            zip_buffer = io.BytesIO()
            with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
                zf.writestr("document.txt", "Sample demo document content.")
                zf.writestr("report.docx", "Sample Word document placeholder.")
                zf.writestr("image.png", "PNG placeholder data.")
            zip_buffer.seek(0)
            with open(sample_zip_path, "wb") as f:
                f.write(zip_buffer.read())
            self.stdout.write(
                self.style.SUCCESS(f"Created sample ZIP file: {sample_zip_path}")
            )
        else:
            self.stdout.write(
                self.style.WARNING(f"Sample ZIP already exists: {sample_zip_path}")
            )

        self.stdout.write(self.style.SUCCESS("Demo data seeding complete."))
