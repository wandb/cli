pipeline {
    node("k8s") {
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
}
