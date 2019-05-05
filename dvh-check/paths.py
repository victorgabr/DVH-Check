from os.path import join, dirname

SCRIPT_DIR = dirname(__file__)
PROTOCOL_DIR = join(SCRIPT_DIR, 'protocols')
INBOX_DIR = join(SCRIPT_DIR, 'test_files')
ALIASES_FILE = join(PROTOCOL_DIR, 'aliases.csv')
