properties([pipelineTriggers([githubPush()])])
node {
    git url: 'https://github.com/a866325272/line-bot',
    branch: 'main'
}
pipeline {
    agent any
    stages {
        stage('Build') {
            steps {
                sh "echo 'start building...'"
                withCredentials([string(credentialsId: 'line-bot_ACCESS_TOKEN', variable: 'ACCESS_TOKEN'), string(credentialsId: 'line-bot_CWB_TOKEN', variable: 'CWB_TOKEN'), string(credentialsId: 'line-bot_EPA_TOKEN', variable: 'EPA_TOKEN'), string(credentialsId: 'line-bot_OPENAI_TOKEN', variable: 'OPENAI_TOKEN'), string(credentialsId: 'line-bot_SECRET', variable: 'SECRET'), string(credentialsId: 'gitlab-container-repo', variable: 'REPO_URL')]) {
                    sh '''docker build -t ${REPO_URL}/jeff/line-bot:latest \
                    --no-cache \
                    --build-arg  ACCESS_TOKEN=${ACCESS_TOKEN} \
                    --build-arg  CWB_TOKEN=${CWB_TOKEN} \
                    --build-arg  EPA_TOKEN=${EPA_TOKEN} \
                    --build-arg  OPENAI_TOKEN=${OPENAI_TOKEN} \
                    --build-arg  SECRET=${SECRET} \
                    .'''
                }
            }
        }
        stage('Push') {
            steps {
                sh "echo 'start pushing...'"
                withCredentials([usernamePassword(credentialsId: 'gitlab-jeff', passwordVariable: 'PASSWORD', usernameVariable: 'USERNAME'), string(credentialsId: 'gitlab-container-repo', variable: 'REPO_URL')]) {
                    sh "docker login -u ${USERNAME} -p ${PASSWORD} ${REPO_URL}"
                    sh "docker push ${REPO_URL}/jeff/line-bot:latest"
                    sh "docker tag ${REPO_URL}/jeff/line-bot:latest ${REPO_URL}/jeff/line-bot:1.0.${BUILD_NUMBER}"
                    sh "docker push ${REPO_URL}/jeff/line-bot:1.0.${BUILD_NUMBER}"
                    sh "docker rmi ${REPO_URL}/jeff/line-bot:latest"
                }
            }
        }
        stage('Deploy') {
            steps {
                sh "echo 'start deploying...'"
                sh "ssh -i /var/jenkins_home/.ssh/id_rsa root@192.168.8.110 /usr/local/bin/docker-compose -f /volume1/docker/docker-compose-line-bot.yml down"
                sh '''docker images | grep gitlab.jeffdomain.com:1005/jeff/line-bot | awk '{print $3}' | xargs docker rmi'''
                sh "ssh -i /var/jenkins_home/.ssh/id_rsa root@192.168.8.110 sed -i 's+gitlab.jeffdomain.com:1005/jeff/line-bot.*+gitlab.jeffdomain.com:1005/jeff/line-bot:1.0.${BUILD_NUMBER}+g' /volume1/docker/docker-compose-line-bot.yml"
                sh "ssh -i /var/jenkins_home/.ssh/id_rsa root@192.168.8.110 /usr/local/bin/docker-compose -f /volume1/docker/docker-compose-line-bot.yml up -d"
                sh "curl -s 192.168.8.110:4040/api/tunnels"
            }
        }
    }
}