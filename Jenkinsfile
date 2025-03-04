pipeline {
    agent any
    stages {
        stage('Post Build') {
            steps {
                sh "echo 'start docker login...'"
                withCredentials([usernamePassword(credentialsId: 'gitlab-jeff', passwordVariable: 'PASSWORD', usernameVariable: 'USERNAME')]) {
                    sh "docker login -u ${USERNAME} -p ${PASSWORD} ${REPO_URL}"
                }
            }
        }
        stage('Build') {
            steps {
                sh "echo 'start building...'"
                sh '''docker build -t ${REPO_URL}/jeff/line-bot:latest \
                --no-cache \
                --build-arg  ACCESS_TOKEN=${ACCESS_TOKEN} \
                --build-arg  CWA_TOKEN=${CWA_TOKEN} \
                --build-arg  EPA_TOKEN=${EPA_TOKEN} \
                --build-arg  OPENAI_TOKEN=${OPENAI_TOKEN} \
                --build-arg  SECRET=${SECRET} \
                --build-arg  GOOGLE_APPLICATION_CREDENTIALS=${GOOGLE_APPLICATION_CREDENTIALS} \
                --build-arg  LOG_PATH=${LOG_PATH} \
                --build-arg  GMAP_API_KEY=${GMAP_API_KEY} \
                .'''
            }
        }
        stage('Push') {
            steps {
                sh "echo 'start pushing...'"
                sh "docker push ${REPO_URL}/jeff/line-bot:latest"
                sh "docker tag ${REPO_URL}/jeff/line-bot:latest ${REPO_URL}/jeff/line-bot:${MAJOR_VERSION}.${BUILD_NUMBER}"
                sh "docker push ${REPO_URL}/jeff/line-bot:${MAJOR_VERSION}.${BUILD_NUMBER}"
                sh "docker rmi ${REPO_URL}/jeff/line-bot:latest"
            }
        }
        stage('Deploy') {
            steps {
                sh "echo 'start deploying...'"
                withCredentials([usernamePassword(credentialsId: 'gitlab-jeff', passwordVariable: 'PASSWORD', usernameVariable: 'USERNAME')]) {
                    sh "ssh -i ${SSH_KEY} root@${DEPLOY_DEST} /usr/local/bin/docker login -u ${USERNAME} -p ${PASSWORD} ${REPO_URL}"
                }
                sh "ssh -i ${SSH_KEY} root@${DEPLOY_DEST} /usr/local/bin/docker-compose -f ${DOCKER_COMPOSE_FILE} down"
                sh '''docker images | grep ${REPO_URL}/jeff/line-bot | awk '{print $3}' | xargs docker rmi'''
                sh "ssh -i ${SSH_KEY} root@${DEPLOY_DEST} sed -i 's+${REPO_URL}/jeff/line-bot.*+${REPO_URL}/jeff/line-bot:${MAJOR_VERSION}.${BUILD_NUMBER}+g' ${DOCKER_COMPOSE_FILE}"
                sh "ssh -i ${SSH_KEY} root@${DEPLOY_DEST} /usr/local/bin/docker-compose -f ${DOCKER_COMPOSE_FILE} up -d"
            }
        }
        /*stage("Get Service URL") {
            steps {
                script {
                    final String url = "${DEPLOY_DEST}:4040/api/tunnels"
                    final String response = sh(script: "curl -s $url", returnStdout: true).trim()
                    echo response
                }
            }
        }*/
    }
}