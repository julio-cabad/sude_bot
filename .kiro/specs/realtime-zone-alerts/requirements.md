# Requirements Document

## Introduction

This feature implements a real-time zone detection and alert system that monitors cryptocurrency markets for newly formed Smart Money Concept zones. The system adapts to any timeframe (1min, 5min, 1h, etc.) and provides immediate alerts when new supply/demand zones are detected, showing the 1-2 most recent zones with detailed information.

## Requirements

### Requirement 1

**User Story:** As a trader, I want to receive real-time alerts when new SMC zones are detected, so that I can react quickly to market structure changes.

#### Acceptance Criteria

1. WHEN a new zone is detected THEN the system SHALL generate an immediate alert
2. WHEN multiple zones are detected simultaneously THEN the system SHALL show the 2 most recent zones
3. WHEN no new zones are found THEN the system SHALL continue monitoring without alerts
4. IF a zone already exists THEN the system SHALL NOT generate duplicate alerts

### Requirement 2

**User Story:** As a trader, I want the system to work with any timeframe I choose, so that I can monitor markets at my preferred intervals.

#### Acceptance Criteria

1. WHEN I set a 1-minute timeframe THEN the system SHALL check for new zones every minute
2. WHEN I set a 5-minute timeframe THEN the system SHALL check for new zones every 5 minutes
3. WHEN I set any valid timeframe THEN the system SHALL adapt automatically
4. IF an invalid timeframe is provided THEN the system SHALL show an error message

### Requirement 3

**User Story:** As a trader, I want to see detailed information about new zones, so that I can make informed trading decisions.

#### Acceptance Criteria

1. WHEN a new zone is detected THEN the system SHALL display the zone type (SUPPLY/DEMAND)
2. WHEN a new zone is detected THEN the system SHALL show the POI (Point of Interest) price
3. WHEN a new zone is detected THEN the system SHALL display the zone range (top/bottom)
4. WHEN a new zone is detected THEN the system SHALL show the formation timestamp
5. WHEN a new zone is detected THEN the system SHALL display distance from current price

### Requirement 4

**User Story:** As a trader, I want to monitor multiple cryptocurrency symbols simultaneously, so that I can catch opportunities across different markets.

#### Acceptance Criteria

1. WHEN monitoring multiple symbols THEN the system SHALL check each symbol independently
2. WHEN a new zone is found in any symbol THEN the system SHALL specify which symbol in the alert
3. WHEN multiple symbols have new zones THEN the system SHALL show alerts for each symbol
4. IF a symbol fails to load data THEN the system SHALL continue monitoring other symbols

### Requirement 5

**User Story:** As a trader, I want the system to run continuously without manual intervention, so that I don't miss any market opportunities.

#### Acceptance Criteria

1. WHEN the system starts THEN it SHALL run continuously until manually stopped
2. WHEN an error occurs THEN the system SHALL log the error and continue monitoring
3. WHEN API limits are reached THEN the system SHALL implement appropriate delays
4. IF the system crashes THEN it SHALL restart automatically if possible

### Requirement 6

**User Story:** As a trader, I want to see visual alerts that are easy to notice, so that I don't miss important zone formations.

#### Acceptance Criteria

1. WHEN a new zone is detected THEN the system SHALL display a prominent visual alert
2. WHEN showing alerts THEN the system SHALL use clear colors and formatting
3. WHEN multiple alerts occur THEN the system SHALL display them in chronological order
4. WHEN an alert is shown THEN it SHALL include a timestamp in local timezone

### Requirement 7

**User Story:** As a trader, I want the system to be efficient and not overload the API, so that it runs reliably without hitting rate limits.

#### Acceptance Criteria

1. WHEN making API calls THEN the system SHALL implement appropriate rate limiting
2. WHEN storing zone data THEN the system SHALL use efficient caching mechanisms
3. WHEN comparing zones THEN the system SHALL use optimized algorithms
4. IF rate limits are approached THEN the system SHALL automatically adjust request frequency

### Requirement 8

**User Story:** As a trader, I want to configure which symbols and timeframes to monitor, so that I can customize the system to my trading strategy.

#### Acceptance Criteria

1. WHEN starting the system THEN I SHALL be able to specify symbols to monitor
2. WHEN starting the system THEN I SHALL be able to set the monitoring timeframe
3. WHEN the system is running THEN I SHALL be able to add or remove symbols dynamically
4. IF invalid configuration is provided THEN the system SHALL show clear error messages