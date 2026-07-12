# Methodology

## Feature Preprocessing
Recency, Frequency, and Monetary Value typically exhibit a heavy right-skewed distribution. K-Means clustering is highly sensitive to variance and distance, so we log-transform these features using `np.log1p()` before clustering. We then apply `StandardScaler` to ensure they have zero mean and unit variance.

## K-Selection
We evaluated $K$ using both the Elbow Method (inertia) and the Silhouette Score across a range of $K \in [2, 10]$.
- The Elbow plot indicated an inflection point around $K=3$ or $K=4$.
- The Silhouette Score peaked at $K=2$, but $K=4$ also showed strong cohesion and separation while providing more actionable, distinct business segments. 

Thus, $K=4$ was selected as the optimal balance between mathematical fit and business utility.

## Segment Naming
We rank each cluster dynamically by average RFM values:
1. **Champions**: Best recency, frequency, and monetary scores.
2. **Loyal Customers**: Good frequency and monetary scores, but possibly slightly worse recency than champions.
3. **At-Risk High-Value**: Poor recency, but high monetary value. We need to win them back to avoid churning high revenue.
4. **Hibernating**: Poor on all metrics. Minimal marketing spend recommended.
