pipeline {
    agent any

    options {
        skipDefaultCheckout(true)
        disableConcurrentBuilds()
    }

    stages {
        stage('Checkout') {
            steps {
                checkout scm
            }
        }

        stage('Build documentation site') {
            steps {
                script {
                    if (isUnix()) {
                        sh 'python3 -m pip install --user markdown'
                        sh 'python3 scripts/build_readme_site.py'
                    } else {
                        bat 'python -m pip install markdown'
                        bat 'python scripts\\build_readme_site.py'
                    }
                }
            }
        }

        stage('Verify site') {
            steps {
                script {
                    if (isUnix()) {
                        sh 'test -s site/index.html'
                    } else {
                        bat 'if not exist site\\index.html exit /b 1'
                    }
                }
            }
        }

        stage('Archive site') {
            steps {
                archiveArtifacts artifacts: 'site/**', fingerprint: true
            }
        }
    }

    post {
        success {
            echo 'Documentation site built successfully. Open the archived site/index.html artifact.'
        }
    }
}