pipeline {
    agent any
    stages {
        stage('Docker Login') {
            steps {
                withCredentials([usernamePassword(credentialsId: 'gitlab-jeff', passwordVariable: 'PASSWORD', usernameVariable: 'USERNAME')]) {
                    sh "docker login -u ${USERNAME} -p ${PASSWORD} ${REPO_URL}"
                }
            }
        }

        // Main App - 永遠執行
        stage('Build Main App') {
            steps {
                sh "echo 'start building main app...'"
                sh '''docker build -t ${REPO_URL}/jeff/line-bot:${MAJOR_VERSION}.${BUILD_NUMBER} \
                    --no-cache \
                    --build-arg ACCESS_TOKEN=${ACCESS_TOKEN} \
                    --build-arg CWA_TOKEN=${CWA_TOKEN} \
                    --build-arg EPA_TOKEN=${EPA_TOKEN} \
                    --build-arg OPENAI_TOKEN=${OPENAI_TOKEN} \
                    --build-arg SECRET=${SECRET} \
                    --build-arg GOOGLE_APPLICATION_CREDENTIALS=${GOOGLE_APPLICATION_CREDENTIALS} \
                    --build-arg LOG_PATH=${LOG_PATH} \
                    --build-arg GMAP_API_KEY=${GMAP_API_KEY} \
                    --build-arg JWT_SECRET_KEY=${JWT_SECRET_KEY} \
                    .'''
            }
        }
        stage('Push Main App') {
            steps {
                sh "docker push ${REPO_URL}/jeff/line-bot:${MAJOR_VERSION}.${BUILD_NUMBER}"
                sh "docker tag ${REPO_URL}/jeff/line-bot:${MAJOR_VERSION}.${BUILD_NUMBER} ${REPO_URL}/jeff/line-bot:latest"
                sh "docker push ${REPO_URL}/jeff/line-bot:latest"
                sh "docker rmi ${REPO_URL}/jeff/line-bot:${MAJOR_VERSION}.${BUILD_NUMBER} || true"
                sh "docker rmi ${REPO_URL}/jeff/line-bot:latest || true"
            }
        }
        stage('Deploy Main App') {
            steps {
                sh "echo 'deploying main app...'"
                sh "ssh -i ${SSH_KEY} root@${DEPLOY_DEST} sed -i 's+${REPO_URL}/jeff/line-bot:.*+${REPO_URL}/jeff/line-bot:${MAJOR_VERSION}.${BUILD_NUMBER}+g' ${DOCKER_COMPOSE_FILE}"
                sh "ssh -i ${SSH_KEY} root@${DEPLOY_DEST} /usr/local/bin/docker-compose -f ${DOCKER_COMPOSE_FILE} pull line-bot"
                sh "ssh -i ${SSH_KEY} root@${DEPLOY_DEST} /usr/local/bin/docker-compose -f ${DOCKER_COMPOSE_FILE} up -d --no-deps line-bot"
            }
        }

        // Screenshot Service - 只在相關檔案有改動時才執行
        stage('Build Screenshot Service') {
            when {
                anyOf {
                    changeset "screenshot-service/**"
                    changeset "Dockerfile.screenshot"
                }
            }
            steps {
                sh "echo 'start building screenshot service...'"
                sh '''docker build -t ${REPO_URL}/jeff/line-bot/screenshot-service:${MAJOR_VERSION}.${BUILD_NUMBER} \
                    --no-cache \
                    -f Dockerfile.screenshot .'''
            }
        }
        stage('Push Screenshot Service') {
            when {
                anyOf {
                    changeset "screenshot-service/**"
                    changeset "Dockerfile.screenshot"
                }
            }
            steps {
                sh "docker push ${REPO_URL}/jeff/line-bot/screenshot-service:${MAJOR_VERSION}.${BUILD_NUMBER}"
                sh "docker tag ${REPO_URL}/jeff/line-bot/screenshot-service:${MAJOR_VERSION}.${BUILD_NUMBER} ${REPO_URL}/jeff/line-bot/screenshot-service:latest"
                sh "docker push ${REPO_URL}/jeff/line-bot/screenshot-service:latest"
                sh "docker rmi ${REPO_URL}/jeff/line-bot/screenshot-service:${MAJOR_VERSION}.${BUILD_NUMBER} || true"
                sh "docker rmi ${REPO_URL}/jeff/line-bot/screenshot-service:latest || true"
            }
        }
        stage('Deploy Screenshot Service') {
            when {
                anyOf {
                    changeset "screenshot-service/**"
                    changeset "Dockerfile.screenshot"
                }
            }
            steps {
                sh "echo 'deploying screenshot service...'"
                sh "ssh -i ${SSH_KEY} root@${DEPLOY_DEST} sed -i 's+${REPO_URL}/jeff/line-bot/screenshot-service.*+${REPO_URL}/jeff/line-bot/screenshot-service:${MAJOR_VERSION}.${BUILD_NUMBER}+g' ${DOCKER_COMPOSE_FILE}"
                sh "ssh -i ${SSH_KEY} root@${DEPLOY_DEST} /usr/local/bin/docker-compose -f ${DOCKER_COMPOSE_FILE} pull screenshot-service"
                sh "ssh -i ${SSH_KEY} root@${DEPLOY_DEST} /usr/local/bin/docker-compose -f ${DOCKER_COMPOSE_FILE} up -d --no-deps screenshot-service"
            }
        }

        stage('Cleanup') {
            steps {
                sh "ssh -i ${SSH_KEY} root@${DEPLOY_DEST} /usr/local/bin/docker image prune -f"
            }
        }
    }
}
