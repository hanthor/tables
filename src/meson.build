pkgdatadir = get_option('prefix') / get_option('datadir') / meson.project_name()
moduledir = pkgdatadir / 'tables'
python = import('python')

# Pull in the shared scaffold and install its package next to the app package,
# so both import from pkgdatadir (which the launcher puts on sys.path).
suite_common = subproject('suite-common')
sc_sources = suite_common.get_variable('suite_common_sources')
install_data(sc_sources, install_dir: pkgdatadir / 'suite_common')

conf = configuration_data()
conf.set('PYTHON', python.find_installation('python3').full_path())
conf.set('VERSION', meson.project_version())
conf.set('pkgdatadir', pkgdatadir)

configure_file(
  input: 'tables.in',
  output: 'tables',
  configuration: conf,
  install: true,
  install_dir: get_option('bindir'),
  install_mode: 'rwxr-xr-x',
)

install_data(
  [ '__init__.py', 'main.py', 'window.py' ],
  install_dir: moduledir,
)
