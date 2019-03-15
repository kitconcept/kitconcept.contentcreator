#!groovy

pipeline {

  agent {
    label 'node'
  }

  stages {

    // --- BUILD ---
    stage('Build') {
      parallel {
        stage('Setup') {
          agent {
            label "node"
          }
          steps {
            deleteDir()
            checkout scm
            sh 'make'
          }
        }
        // stage('Static Code Analysis') {
        //   agent {
        //     label "node"
        //   }
        //   steps {
        //     deleteDir()
        //     checkout scm
        //     sh 'make code-analysis'
        //   }
        // }
        stage('Unit / Integration Tests') {
          agent {
            label "node"
          }
          steps {
            deleteDir()
            checkout scm
            sh 'make'
            sh 'make test'
          }
        }
        // stage('Robot Framework based acceptance tests') {
        //   agent {
        //     label "node"
        //   }
        //   steps {
        //     deleteDir()
        //     checkout scm
        //     sh 'make test-acceptance'
        //   }
        // }
      }
    }
  }

  post {
    success {
      slackSend (
        color: 'good',
        message: "SUCCESS: #${env.BUILD_NUMBER} ${env.JOB_NAME} (${env.BUILD_URL})"
      )
    }
    failure {
      slackSend (
        color: 'danger',
        message: "FAILURE: #${env.BUILD_NUMBER} ${env.JOB_NAME} (${env.BUILD_URL})"
      )
    }
    unstable {
      slackSend (
        color: 'warning',
        message: "UNSTABLE: #${env.BUILD_NUMBER} ${env.JOB_NAME} (${env.BUILD_URL})"
      )
    }
    aborted {
      slackSend (
        color: 'danger',
        message: "ABORTED: #${env.BUILD_NUMBER} ${env.JOB_NAME} (${env.BUILD_URL})"
      )
    }
  }
}
