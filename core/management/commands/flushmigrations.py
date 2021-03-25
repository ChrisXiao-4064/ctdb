from django.apps import apps
from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from pathlib import Path


class Command(BaseCommand):
    help = (
        "Delete all migration of Apps directory living in the `settings.BASE_DIR`."
        "This should be used carefully."
    )

    BASE_DIR = settings.BASE_DIR

    def rm_rf(self, path):
        if path.is_file():
            print(path)
            checked = input(
                '\nThese files and directories will be permanently deleted!\n\n'
                "Type 'yes' to continue, or 'no' to cancel: "
            )
            if checked == 'yes':
                path.unlink(missing_ok=False)
            else:
                raise CommandError('Flushing migration files cancelled.')
            return
        files = []
        dirs = []
        for f in path.iterdir():
            if f.is_file():
                files.append(f)
            else:
                dirs.append(f)
        if files:
            for f in files:
                print(f)
            checked = input(
                '\nThese files and directories will be permanently deleted!\n\n'
                "Type 'yes' to continue, or 'no' to cancel: "
            )
            if checked == 'yes':
                for f in files:
                    f.unlink(missing_ok=False)
            else:
                raise CommandError('Flushing migration files cancelled.')
        for d in dirs:
            self.rm_rf(d)

    def handle(self, *app_labels, **options):
        configs = apps.get_app_configs()
        paths = []
        for config in configs:
            path = Path(config.path)
            if path.parent == self.BASE_DIR:
                paths.append(path)
        paths.sort()
        migrationdirs = [path / 'migrations' for path in paths]
        paths = []
        for migrationdir in migrationdirs:
            subdirs = [subdir for subdir in migrationdir.iterdir()]
            targets = [subdir for subdir in subdirs if subdir.name != '__init__.py']
            paths.extend(targets)
        for f in paths:
            self.rm_rf(f)