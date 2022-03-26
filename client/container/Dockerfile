FROM alpine:latest

RUN apk add --update iproute2 iptables bash jq httpie util-linux iperf3 && \
    rm -rf /tmp/* /var/tmp/* /var/cache/apk/* /var/cache/distfiles/*

CMD ["containerue.sh"]

ADD containerue.sh /usr/local/bin/
RUN chmod a+x /usr/local/bin/*
