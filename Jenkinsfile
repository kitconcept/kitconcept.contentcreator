#!groovy

pipeline {

  options {
    buildDiscarder(logRotator(numToKeepStr:'20'))
    skipDefaultCheckout()
    disableConcurrentBuilds()
    timeout(time: 60, unit: 'MINUTES')
  }

  agent {
    label 'node'
  }

  stages {
    stage('Build') {
      steps {
        deleteDir()
        checkout scm
        sh 'make'
      }
    }
    stage('Code Analysis') {
      steps {
        deleteDir()
        checkout scm
        sh 'make'
        sh 'make code-analysis'
        sh 'bin/black  --check src/'
      }
    }
    stage('Test') {
      steps {
        deleteDir()
        checkout scm
        sh 'make'
        sh 'make test'
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
