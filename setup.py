# #!/usr/bin/python3
# jimk: remote machines need the above line when building console scripts which will
# be installed on machines which also require python 2 in their path
from setuptools import setup

setup(name='volume-manifest-tool', version='1.0', packages=['v_m_t'],
      url='https://github.com/buda-base/volume-manifest-tool/', license='', author='jimk/eroux', author_email='',
      description='Creates manifests for syncd works.', entry_points={
        'console_scripts': ['manifestforwork = manifestforwork:manifestShell',
                            'manifestFromS3 = manifestforwork:manifestFromS3']},
      install_requires=['boto3', 'requests', 'lxml', 'pillow', 's3transfer', 'botocore'])
