from __future__ import print_function

import distutils.spawn
import re
from setuptools import find_packages
from setuptools import setup
import shlex
import subprocess
import sys
import yaml


def get_version():
    filename = 'labelme/__init__.py'
    with open(filename) as f:
        match = re.search(
            r'''^__version__ = ['"]([^'"]*)['"]''', f.read(), re.M
        )
    if not match:
        raise RuntimeError("{} doesn't contain __version__".format(filename))
    version = match.groups()[0]
    return version

def update_config_for_version():
    version = get_version()
    config_file = 'labelme/config/default_config.yaml'
    with open(config_file) as f:
        config = yaml.safe_load(f)

    config['version'] = version

    with open(config_file, 'w') as f:
        yaml.dump(config, f)

def get_install_requires():
    PY3 = sys.version_info[0] == 3
    PY2 = sys.version_info[0] == 2
    assert PY3 or PY2

    install_requires = [
        'imgviz>=0.11.0',
        'matplotlib',
        'numpy',
        'Pillow>=2.8.0',
        'PyYAML',
        'qtpy',
        'termcolor',
        'opencv-contrib-python',
    ]

    # Find python binding for qt with priority:
    # PyQt5 -> PySide2 -> PyQt4,
    # and PyQt5 is automatically installed on Python3.
    QT_BINDING = None

    try:
        import PyQt5  # NOQA
        QT_BINDING = 'pyqt5'
    except ImportError:
        pass

    if QT_BINDING is None:
        try:
            import PySide2  # NOQA
            QT_BINDING = 'pyside2'
        except ImportError:
            pass

    if QT_BINDING is None:
        try:
            import PyQt4  # NOQA
            QT_BINDING = 'pyqt4'
        except ImportError:
            if PY2:
                print(
                    'Please install PyQt5, PySide2 or PyQt4 for Python2.\n'
                    'Note that PyQt5 can be installed via pip for Python3.',
                    file=sys.stderr,
                )
                sys.exit(1)
            assert PY3
            # PyQt5 can be installed via pip for Python3
            install_requires.append('PyQt5')
            QT_BINDING = 'pyqt5'
    del QT_BINDING

    return install_requires

def main():
    version = get_version()
    update_config_for_version()

    setup(
        name='smart-labelme',
        version=version,
        packages=find_packages(exclude=['github2pypi']),
        description='Smart Image Annotation with Python',
        long_description="Refer to https://github.com/bhavyaajani/smart-labelme for usage.",
        long_description_content_type='text/markdown',
        author='Bhavya Ajani',
        author_email='ajanibhavya@gmail.com',
        url='https://github.com/bhavyaajani/smart-labelme',
        install_requires=get_install_requires(),
        license='GPLv3',
        keywords='Image Annotation, Machine Learning',
        classifiers=[
            'Development Status :: 5 - Production/Stable',
            'Intended Audience :: Developers',
            'Natural Language :: English',
            'Programming Language :: Python',
            'Programming Language :: Python :: 2.7',
            'Programming Language :: Python :: 3.5',
            'Programming Language :: Python :: 3.6',
            'Programming Language :: Python :: 3.7',
            'Programming Language :: Python :: Implementation :: CPython',
            'Programming Language :: Python :: Implementation :: PyPy',
        ],
        package_data={'labelme': ['icons/*', 'config/*.yaml', 'doc/*']},
        entry_points={
            'console_scripts': [
                'smart_labelme=labelme.__main__:main',
                'smart_labelme_draw_json=labelme.cli.draw_json:main',
                'smart_labelme2mask=labelme.cli.labelme2mask:main',
                'smart_labelme_draw_label_png=labelme.cli.draw_label_png:main',
                'smart_labelme_json_to_dataset=labelme.cli.json_to_dataset:main',
            ],
        },
    )


if __name__ == '__main__':
    main()
