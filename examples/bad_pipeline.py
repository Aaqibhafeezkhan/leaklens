from imblearn.over_sampling import SMOTE
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler

sc = StandardScaler()
X = sc.fit_transform(X)
sm = SMOTE()
X, y = sm.fit_resample(X, y)
X_train, X_test, y_train, y_test = train_test_split(X, y)