pipeline {
    agent {
        docker { image 'themattrix/tox' }
    }
    stages {
        stage('Test') {
            steps {
                sh 'tox'
            }
        }
    }
}
