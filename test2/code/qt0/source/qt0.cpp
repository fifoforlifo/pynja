#include <QtCore/QList>
#include <QtCore/QObject>

class QZero : public QObject
{
    Q_OBJECT
public:
    QZero()
    {
    }
};

int non_qt_function();

int main()
{
    QZero* zero = new QZero();
    delete zero;
    return non_qt_function();
}

#include "qt0.moc"

