from django.apps import AppConfig
from django.db.backends.signals import connection_created


def configure_sqlite(sender, connection, **kwargs):
    if connection.vendor == 'sqlite':
        with connection.cursor() as cursor:
            cursor.execute('PRAGMA journal_mode = WAL;')
            cursor.execute('PRAGMA synchronous = NORMAL;')
            cursor.execute('PRAGMA cache_size = -64000;')   # 64MB RAM cache
            cursor.execute('PRAGMA temp_store = MEMORY;')
            cursor.execute('PRAGMA mmap_size = 268435456;')  # 256MB memory-mapped I/O


class StoreConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'store'

    def ready(self):
        connection_created.connect(configure_sqlite)
