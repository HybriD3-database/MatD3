# import sys
#
# print 'This is the name of the script: ', sys.argv[0]
# print 'Number of arguments: ', len(sys.argv)
# print 'The arguments are: ' , str(sys.argv)
#
# rng = sys.argv[1].strip()
# print 'Second argument: ', rng


def parserange(rng):
    # & <= >= < >
    if rng.find('&') != -1:
        ltindex = rng.find('<')
        mtindex = rng.find('>')
        if ltindex != -1 and mtindex != -1:
            rng = rng.split('&')
            print('New range: ', rng)
            # lowrange = 0
            # highrange = 0
            if ltindex > mtindex:
                lowrangeraw = rng[0]
                highrangeraw = rng[1]
            else:
                lowrangeraw = rng[1]
                highrangeraw = rng[0]
            print(lowrangeraw, highrangeraw)
            if lowrangeraw.find('>=') != -1:
                lowineq = '>='
                lowrange = lowrangeraw.replace('>=', '')
            else:
                lowineq = '>'
                lowrange = lowrangeraw.replace('>', '')
            if highrangeraw.find('<=') != -1:
                highineq = '<='
                highrange = highrangeraw.replace('<=', '')
            else:
                highineq = '<'
                highrange = highrangeraw.replace('<', '')
            print(lowrange, highrange)
            return ['bidirectional', lowrange, highrange, lowineq, highineq]
        else:
            print('Missing conditional')
            return 1
    else:
        # default inequality is '>'
        print('Missing '&'')
        inequality = '>'
        if rng.find('<') != -1:
            inequality = '<'
            if rng.find('<=') != -1:
                inequality += '='
        elif rng.find('>') != -1:
            if rng.find('>=') != -1:
                inequality += '='
        rng = rng.replace(inequality, '')
        print(inequality, rng)
        return ['unidirectional', rng, inequality]
