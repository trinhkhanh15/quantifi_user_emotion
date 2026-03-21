# 🚗 Nền Tảng Hệ Sinh Thái Ô Tô Thông Minh — AutoHub

## MVP Blueprint cho Hackathon $500,000

---

## I. Executive Summary

**AutoHub** là nền tảng "Super App" cho hệ sinh thái ô tô, kết hợp 3 trụ cột: **Social Intelligence** (cộng đồng kỹ thuật AI-driven), **Digital Twin Garage** (bản sao số của phương tiện), và **Marketplace-as-a-Service** (sàn giao dịch dịch vụ & phụ tùng). Nền tảng giải quyết bài toán phân mảnh thông tin và trải nghiệm sở hữu xe, nơi mà hiện tại chủ xe phải sử dụng 5-7 ứng dụng riêng biệt cho các nhu cầu khác nhau.

**Tầm nhìn:** Trở thành "Operating System" cho trải nghiệm sở hữu xe tại Việt Nam, sau đó mở rộng sang Đông Nam Á.

---

## II. Kiến Trúc Sản Phẩm (Product Architecture)

### 2.1. System Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                        CLIENT LAYER                             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐  │
│  │  Mobile App   │  │   Web App    │  │  Provider Dashboard  │  │
│  │ (React Native)│  │  (Next.js)   │  │     (Next.js)        │  │
│  └──────┬───────┘  └──────┬───────┘  └──────────┬───────────┘  │
└─────────┼──────────────────┼────────────────────┼───────────────┘
          │                  │                    │
┌─────────▼──────────────────▼────────────────────▼───────────────┐
│                      API GATEWAY (Kong/AWS)                      │
│              Rate Limiting · Auth · Load Balancing               │
└─────────┬──────────────────┬────────────────────┬───────────────┘
          │                  │                    │
┌─────────▼──────────────────▼────────────────────▼───────────────┐
│                    MICROSERVICES LAYER                           │
│  ┌─────────┐ ┌──────────┐ ┌─────────┐ ┌──────────┐ ┌────────┐ │
│  │  User   │ │ Vehicle  │ │  Feed   │ │Marketplace│ │Booking │ │
│  │ Service │ │ Service  │ │ Service │ │  Service  │ │Service │ │
│  └────┬────┘ └────┬─────┘ └────┬────┘ └────┬─────┘ └───┬────┘ │
│  ┌────┴────┐ ┌────┴─────┐ ┌────┴────┐ ┌────┴─────┐ ┌───┴────┐ │
│  │Notifi-  │ │   AI     │ │ Payment │ │  Review  │ │ Wash   │ │
│  │cation   │ │ Engine   │ │ Service │ │  Service │ │Service │ │
│  └─────────┘ └──────────┘ └─────────┘ └──────────┘ └────────┘ │
└─────────┬──────────────────┬────────────────────┬───────────────┘
          │                  │                    │
┌─────────▼──────────────────▼────────────────────▼───────────────┐
│                      DATA LAYER                                  │
│  ┌──────────┐  ┌───────────┐  ┌─────────┐  ┌────────────────┐  │
│  │PostgreSQL│  │   Redis   │  │   S3    │  │ Elasticsearch  │  │
│  │ (Master) │  │  (Cache)  │  │ (Media) │  │   (Search)     │  │
│  └──────────┘  └───────────┘  └─────────┘  └────────────────┘  │
│  ┌──────────────────┐  ┌──────────────────────────────────────┐ │
│  │  Vector DB       │  │     Message Queue (RabbitMQ/Kafka)   │ │
│  │  (Pinecone/PGV)  │  │                                      │ │
│  └──────────────────┘  └──────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

### 2.2. Tech Stack Selection

| Layer | Technology | Justification |
|-------|-----------|---------------|
| **Mobile** | React Native + Expo | Cross-platform, single codebase, nhanh cho MVP |
| **Web Frontend** | Next.js 14 (App Router) | SSR/SSG cho SEO, React Server Components |
| **API Gateway** | Kong / AWS API Gateway | Rate limiting, auth, analytics built-in |
| **Backend** | Node.js (NestJS) | TypeScript end-to-end, decorator-based DI, microservice-ready |
| **Database** | PostgreSQL + PostGIS | Relational + Geospatial queries cho location-based services |
| **Cache** | Redis | Session, feed caching, real-time data |
| **Search** | Elasticsearch | Full-text search phụ tùng, dịch vụ, bài viết |
| **AI/ML** | Python (FastAPI) + OpenAI API | Recommendation engine, NLP cho feed & chatbot |
| **Vector DB** | Pinecone / pgvector | Semantic search, AI embeddings |
| **Message Queue** | RabbitMQ (MVP) → Kafka (Scale) | Async processing, event-driven architecture |
| **Storage** | AWS S3 + CloudFront | Media files, CDN |
| **Payment** | VNPay + MoMo + ZaloPay SDK | Phổ biến tại VN |
| **CI/CD** | GitHub Actions + Docker + AWS ECS | Automated deployment |
| **Monitoring** | Datadog / Grafana + Prometheus | Observability |

---

## III. Chi Tiết Tính Năng & Implementation

### 3.1. Dashboard — AI-Driven Social Feed

<details>
<summary><strong>📐 Data Model & Schema</strong></summary>

```sql
-- Posts table
CREATE TABLE posts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    author_id UUID NOT NULL REFERENCES users(id),
    content TEXT NOT NULL,
    post_type VARCHAR(20) CHECK (post_type IN (
        'technical_issue', 'experience', 'review', 
        'tip', 'question', 'showcase'
    )),
    vehicle_context JSONB, -- {make, model, year, mileage, issue_category}
    media_urls TEXT[],
    tags TEXT[],
    embedding VECTOR(1536), -- OpenAI ada-002 embedding
    like_count INT DEFAULT 0,
    comment_count INT DEFAULT 0,
    share_count INT DEFAULT 0,
    is_verified_solution BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Feed scoring table (materialized)
CREATE TABLE feed_scores (
    user_id UUID REFERENCES users(id),
    post_id UUID REFERENCES posts(id),
    relevance_score FLOAT, -- AI-computed
    recency_score FLOAT,
    engagement_score FLOAT,
    final_score FLOAT GENERATED ALWAYS AS (
        relevance_score * 0.5 + recency_score * 0.3 + engagement_score * 0.2
    ) STORED,
    computed_at TIMESTAMPTZ DEFAULT NOW(),
    PRIMARY KEY (user_id, post_id)
);

-- Interactions
CREATE TABLE post_interactions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id),
    post_id UUID NOT NULL REFERENCES posts(id),
    interaction_type VARCHAR(10) CHECK (interaction_type IN ('like', 'comment', 'share', 'save', 'report')),
    content TEXT, -- for comments
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_posts_embedding ON posts USING ivfflat (embedding vector_cosine_ops);
CREATE INDEX idx_posts_tags ON posts USING GIN (tags);
CREATE INDEX idx_feed_scores_user ON feed_scores (user_id, final_score DESC);
```

</details>

#### AI Feed Ranking Algorithm

```python
# services/ai-engine/feed_ranker.py
from dataclasses import dataclass
from typing import List
import numpy as np
from openai import OpenAI

@dataclass
class UserContext:
    user_id: str
    role: str  # 'customer' | 'provider'
    vehicles: List[dict]  # [{make, model, year, mileage}]
    interaction_history: List[str]  # post_ids interacted with
    interests: List[str]  # derived topics
    location: tuple  # (lat, lng)

@dataclass 
class PostCandidate:
    post_id: str
    embedding: np.ndarray
    post_type: str
    vehicle_context: dict
    engagement_metrics: dict
    created_at: float
    author_reputation: float

class AIFeedRanker:
    """
    Multi-stage ranking pipeline:
    1. Candidate Generation (Recall) — retrieve top 200 candidates
    2. Scoring (Ranking) — compute personalized scores
    3. Re-ranking (Diversity) — ensure topic diversity in top 10
    """
    
    def __init__(self, openai_client: OpenAI, vector_db, redis_cache):
        self.openai = openai_client
        self.vector_db = vector_db
        self.cache = redis_cache
    
    async def get_personalized_feed(self, user: UserContext, limit: int = 10) -> List[str]:
        # Check cache first (TTL: 5 minutes)
        cache_key = f"feed:{user.user_id}:v2"
        cached = await self.cache.get(cache_key)
        if cached:
            return cached
        
        # Stage 1: Candidate Generation
        candidates = await self._generate_candidates(user, pool_size=200)
        
        # Stage 2: Personalized Scoring
        scored = await self._score_candidates(user, candidates)
        
        # Stage 3: Diversity Re-ranking (MMR - Maximal Marginal Relevance)
        final = self._mmr_rerank(scored, limit=limit, lambda_param=0.7)
        
        # Cache result
        result = [p.post_id for p in final]
        await self.cache.set(cache_key, result, ttl=300)
        return result
    
    async def _generate_candidates(self, user: UserContext, pool_size: int) -> List[PostCandidate]:
        """Multi-signal candidate retrieval"""
        candidates = set()
        
        # Signal 1: Vehicle-based similarity (semantic search)
        for vehicle in user.vehicles:
            vehicle_query = f"{vehicle['make']} {vehicle['model']} {vehicle['year']}"
            query_embedding = await self._get_embedding(vehicle_query)
            similar = await self.vector_db.query(
                vector=query_embedding,
                top_k=pool_size // 3,
                filter={"created_after": self._days_ago(30)}
            )
            candidates.update(similar)
        
        # Signal 2: Interest-based (collaborative filtering)
        interest_posts = await self._get_interest_based(user, limit=pool_size // 3)
        candidates.update(interest_posts)
        
        # Signal 3: Trending in user's vehicle community
        trending = await self._get_trending(user.vehicles, limit=pool_size // 3)
        candidates.update(trending)
        
        return list(candidates)[:pool_size]
    
    async def _score_candidates(self, user: UserContext, candidates: List[PostCandidate]) -> List[PostCandidate]:
        """Compute final score with weighted signals"""
        user_embedding = await self._get_user_profile_embedding(user)
        
        for candidate in candidates:
            # Relevance: cosine similarity between user profile and post
            relevance = np.dot(user_embedding, candidate.embedding) / (
                np.linalg.norm(user_embedding) * np.linalg.norm(candidate.embedding)
            )
            
            # Recency: exponential decay (half-life = 24 hours)
            hours_old = (time.time() - candidate.created_at) / 3600
            recency = np.exp(-0.029 * hours_old)  # ln(2)/24
            
            # Engagement: normalized engagement rate
            total = sum(candidate.engagement_metrics.values()) + 1
            engagement = np.log1p(total) / 10
            
            # Vehicle match bonus
            vehicle_bonus = self._compute_vehicle_match(user.vehicles, candidate.vehicle_context)
            
            # Role-specific boost
            role_boost = self._role_boost(user.role, candidate.post_type)
            
            # Final weighted score
            candidate.score = (
                relevance * 0.35 +
                recency * 0.25 +
                engagement * 0.15 +
                vehicle_bonus * 0.15 +
                role_boost * 0.05 +
                candidate.author_reputation * 0.05
            )
        
        return sorted(candidates, key=lambda x: x.score, reverse=True)
    
    def _mmr_rerank(self, scored: List[PostCandidate], limit: int, lambda_param: float) -> List[PostCandidate]:
        """Maximal Marginal Relevance for diversity"""
        selected = [scored[0]]
        remaining = scored[1:]
        
        while len(selected) < limit and remaining:
            best_score = -float('inf')
            best_idx = 0
            
            for i, candidate in enumerate(remaining):
                # Max similarity to already selected posts
                max_sim = max(
                    np.dot(candidate.embedding, s.embedding) / (
                        np.linalg.norm(candidate.embedding) * np.linalg.norm(s.embedding)
                    )
                    for s in selected
                )
                
                # MMR score = λ * relevance - (1-λ) * max_similarity_to_selected
                mmr = lambda_param * candidate.score - (1 - lambda_param) * max_sim
                
                if mmr > best_score:
                    best_score = mmr
                    best_idx = i
            
            selected.append(remaining.pop(best_idx))
        
        return selected
    
    def _role_boost(self, role: str, post_type: str) -> float:
        """Boost certain content types based on user role"""
        boosts = {
            'customer': {
                'technical_issue': 0.8, 'experience': 0.7, 'tip': 0.9,
                'review': 0.6, 'question': 0.5, 'showcase': 0.4
            },
            'provider': {
                'technical_issue': 0.9, 'question': 0.8, 'review': 0.7,
                'experience': 0.5, 'tip': 0.6, 'showcase': 0.3
            }
        }
        return boosts.get(role, {}).get(post_type, 0.5)
```

#### Feed API Endpoint

```typescript
// backend/src/modules/feed/feed.controller.ts
import { Controller, Get, Query, UseGuards, Req } from '@nestjs/common';
import { AuthGuard } from '@nestjs/passport';
import { FeedService } from './feed.service';
import { ApiTags, ApiOperation, ApiBearerAuth } from '@nestjs/swagger';

@ApiTags('Feed')
@Controller('api/v1/feed')
@UseGuards(AuthGuard('jwt'))
@ApiBearerAuth()
export class FeedController {
  constructor(private readonly feedService: FeedService) {}

  @Get()
  @ApiOperation({ summary: 'Get personalized AI-driven feed' })
  async getPersonalizedFeed(
    @Req() req,
    @Query('page') page: number = 1,
    @Query('limit') limit: number = 10,
  ) {
    const userId = req.user.id;
    
    // Fetch personalized feed from AI ranking service
    const feed = await this.feedService.getPersonalizedFeed(userId, {
      page,
      limit,
      includePromoted: true,
    });

    return {
      success: true,
      data: {
        posts: feed.posts,
        pagination: {
          page,
          limit,
          total: feed.total,
          hasNext: feed.hasNext,
        },
        meta: {
          algorithm_version: 'v2.1',
          personalization_signals: feed.signals, // transparency
        },
      },
    };
  }

  @Get('trending')
  @ApiOperation({ summary: 'Get trending posts in vehicle community' })
  async getTrending(
    @Query('vehicle_make') make?: string,
    @Query('vehicle_model') model?: string,
    @Query('timeframe') timeframe: string = '24h',
  ) {
    return this.feedService.getTrending({ make, model, timeframe });
  }
}
```

---

### 3.2. Marketplace — E-commerce Engine

<details>
<summary><strong>📐 Data Model</strong></summary>

```sql
-- Products
CREATE TABLE products (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    provider_id UUID NOT NULL REFERENCES providers(id),
    name VARCHAR(500) NOT NULL,
    slug VARCHAR(500) UNIQUE,
    description TEXT,
    category_id UUID REFERENCES categories(id),
    
    -- Pricing
    base_price DECIMAL(12,2) NOT NULL,
    sale_price DECIMAL(12,2),
    currency VARCHAR(3) DEFAULT 'VND',
    
    -- Vehicle compatibility
    compatible_vehicles JSONB, -- [{make, model, year_from, year_to, engine}]
    oem_part_number VARCHAR(100),
    
    -- Attributes
    attributes JSONB, -- {brand, origin, warranty_months, weight_kg}
    
    -- Media
    images TEXT[],
    
    -- Search & AI
    search_vector TSVECTOR GENERATED ALWAYS AS (
        setweight(to_tsvector('simple', coalesce(name, '')), 'A') ||
        setweight(to_tsvector('simple', coalesce(description, '')), 'B') ||
        setweight(to_tsvector('simple', coalesce(oem_part_number, '')), 'A')
    ) STORED,
    embedding VECTOR(1536),
    
    -- Stats
    avg_rating DECIMAL(2,1) DEFAULT 0,
    review_count INT DEFAULT 0,
    sold_count INT DEFAULT 0,
    
    -- Status
    status VARCHAR(20) DEFAULT 'active',
    stock_quantity INT DEFAULT 0,
    
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Orders
CREATE TABLE orders (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    order_number VARCHAR(20) UNIQUE NOT NULL,
    customer_id UUID NOT NULL REFERENCES users(id),
    provider_id UUID NOT NULL REFERENCES providers(id),
    
    -- Items stored as JSONB for historical integrity
    items JSONB NOT NULL -- [{product_id, name, quantity, unit_price, total}]
    
    subtotal DECIMAL(12,2) NOT NULL,
    shipping_fee DECIMAL(12,2) DEFAULT 0,
    platform_fee DECIMAL(12,2) DEFAULT 0, -- commission
    discount DECIMAL(12,2) DEFAULT 0,
    total DECIMAL(12,2) NOT NULL,
    
    -- Shipping
    shipping_address JSONB,
    shipping_method VARCHAR(50),
    tracking_number VARCHAR(100),
    
    -- Status
    status VARCHAR(20) DEFAULT 'pending' CHECK (status IN (
        'pending', 'confirmed', 'processing', 'shipped', 
        'delivered', 'completed', 'cancelled', 'refunded'
    )),
    
    payment_status VARCHAR(20) DEFAULT 'unpaid',
    payment_method VARCHAR(50),
    payment_reference VARCHAR(200),
    
    -- Vehicle context (which car is this for?)
    vehicle_id UUID REFERENCES vehicles(id),
    
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_products_search ON products USING GIN (search_vector);
CREATE INDEX idx_products_compatible ON products USING GIN (compatible_vehicles);
CREATE INDEX idx_products_embedding ON products USING ivfflat (embedding vector_cosine_ops);
CREATE INDEX idx_orders_customer ON orders (customer_id, created_at DESC);
CREATE INDEX idx_orders_provider ON orders (provider_id, status);
```

</details>

#### AI Recommender System

```python
# services/ai-engine/recommender.py
from typing import List, Dict, Optional
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

class AutoPartsRecommender:
    """
    Hybrid Recommendation Engine combining:
    1. Content-based filtering (vehicle compatibility + embeddings)
    2. Collaborative filtering (user behavior patterns)
    3. Context-aware recommendations (vehicle condition signals)
    """
    
    def __init__(self, db, vector_store, openai_client):
        self.db = db
        self.vectors = vector_store
        self.openai = openai_client
    
    async def get_recommendations(
        self,
        user_id: str,
        context: Optional[Dict] = None,
        limit: int = 20
    ) -> List[Dict]:
        """
        Main recommendation pipeline.
        
        Context can include:
        - vehicle_id: specific vehicle being serviced
        - current_mileage: triggers mileage-based recommendations
        - recent_issue: text description of a problem
        - page_context: 'feed', 'vehicle_profile', 'post_detail'
        """
        user_profile = await self._build_user_profile(user_id)
        
        # Generate candidates from multiple sources
        candidates = []
        
        # Source 1: Vehicle-compatible products
        if user_profile.get('vehicles'):
            compat = await self._vehicle_compatible_products(
                user_profile['vehicles'], limit=50
            )
            candidates.extend(compat)
        
        # Source 2: Mileage-based maintenance products
        if context and context.get('current_mileage'):
            mileage_recs = await self._mileage_based_recommendations(
                user_profile['vehicles'],
                context['current_mileage']
            )
            candidates.extend(mileage_recs)
        
        # Source 3: Issue-based recommendations
        if context and context.get('recent_issue'):
            issue_recs = await self._issue_based_recommendations(
                context['recent_issue'],
                user_profile['vehicles']
            )
            candidates.extend(issue_recs)
        
        # Source 4: Collaborative filtering
        cf_recs = await self._collaborative_filter(user_id, limit=30)
        candidates.extend(cf_recs)
        
        # Deduplicate and score
        unique_candidates = self._deduplicate(candidates)
        scored = await self._rank_candidates(user_profile, unique_candidates)
        
        return scored[:limit]
    
    async def _mileage_based_recommendations(
        self, vehicles: List[Dict], current_mileage: int
    ) -> List[Dict]:
        """
        Recommend maintenance products based on mileage intervals.
        
        Standard intervals:
        - Every 5,000 km: Oil filter, engine oil
        - Every 10,000 km: Air filter, cabin filter
        - Every 20,000 km: Brake pads inspection
        - Every 40,000 km: Spark plugs, transmission fluid
        - Every 60,000 km: Timing belt, coolant flush
        """
        maintenance_schedule = {
            5000: ['engine_oil', 'oil_filter'],
            10000: ['air_filter', 'cabin_filter', 'engine_oil', 'oil_filter'],
            20000: ['brake_pads', 'brake_fluid', 'air_filter', 'cabin_filter'],
            40000: ['spark_plugs', 'transmission_fluid', 'power_steering_fluid'],
            60000: ['timing_belt', 'coolant', 'serpentine_belt'],
            100000: ['water_pump', 'alternator', 'suspension_bushings'],
        }
        
        recommendations = []
        for interval, parts in maintenance_schedule.items():
            # Check if user is within 500km of a maintenance interval
            if current_mileage % interval <= 500 or interval - (current_mileage % interval) <= 500:
                for vehicle in vehicles:
                    products = await self.db.query(
                        """
                        SELECT * FROM products 
                        WHERE category_slug = ANY($1)
                        AND compatible_vehicles @> $2::jsonb
                        AND status = 'active'
                        ORDER BY avg_rating DESC, sold_count DESC
                        LIMIT 5
                        """,
                        parts,
                        json.dumps([{"make": vehicle["make"], "model": vehicle["model"]}])
                    )
                    for p in products:
                        p['recommendation_reason'] = f'Recommended at {current_mileage:,}km (every {interval:,}km interval)'
                        p['urgency'] = 'high' if current_mileage % interval <= 500 else 'upcoming'
                    recommendations.extend(products)
        
        return recommendations
    
    async def _issue_based_recommendations(
        self, issue_text: str, vehicles: List[Dict]
    ) -> List[Dict]:
        """Use AI to parse issue description and recommend relevant parts"""
        
        # Step 1: Extract parts/categories from issue description using LLM
        extraction_prompt = f"""
        Given this car issue description, identify the most likely parts/components that need replacement or repair.
        
        Issue: "{issue_text}"
        Vehicle(s): {json.dumps(vehicles)}
        
        Return JSON array of: [{{"part_category": "...", "confidence": 0.0-1.0, "reason": "..."}}]
        """
        
        response = await self.openai.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": extraction_prompt}],
            response_format={"type": "json_object"},
            temperature=0.1
        )
        
        parts_needed = json.loads(response.choices[0].message.content)
        
        # Step 2: Semantic search for matching products
        issue_embedding = await self._get_embedding(issue_text)
        similar_products = await self.vectors.query(
            vector=issue_embedding,
            top_k=20,
            filter={"status": "active"}
        )
        
        # Step 3: Cross-reference with vehicle compatibility
        compatible = [
            p for p in similar_products
            if self._is_vehicle_compatible(p, vehicles)
        ]
        
        for p in compatible:
            p['recommendation_reason'] = f'Suggested for: {issue_text[:100]}'
        
        return compatible
```

---

### 3.3. Provider Hub — Service Booking System

```typescript
// backend/src/modules/booking/booking.service.ts
import { Injectable, BadRequestException } from '@nestjs/common';
import { InjectRepository } from '@nestjs/typeorm';
import { Repository, Between } from 'typeorm';
import { Booking, BookingStatus } from './entities/booking.entity';
import { ProviderSchedule } from './entities/provider-schedule.entity';
import { NotificationService } from '../notification/notification.service';
import { RedisService } from '../common/redis.service';

@Injectable()
export class BookingService {
  constructor(
    @InjectRepository(Booking)
    private bookingRepo: Repository<Booking>,
    @InjectRepository(ProviderSchedule)
    private scheduleRepo: Repository<ProviderSchedule>,
    private notificationService: NotificationService,
    private redis: RedisService,
  ) {}

  async createBooking(dto: CreateBookingDto, customerId: string): Promise<Booking> {
    // 1. Validate time slot availability (with distributed lock)
    const lockKey = `booking:lock:${dto.providerId}:${dto.date}:${dto.timeSlot}`;
    const lock = await this.redis.acquireLock(lockKey, 10000); // 10s TTL
    
    if (!lock) {
      throw new BadRequestException('Time slot is being booked by another user. Please try again.');
    }

    try {
      // 2. Check provider schedule
      const schedule = await this.scheduleRepo.findOne({
        where: {
          providerId: dto.providerId,
          dayOfWeek: new Date(dto.date).getDay(),
          isActive: true,
        },
      });

      if (!schedule) {
        throw new BadRequestException('Provider is not available on this day.');
      }

      // 3. Check existing bookings for this slot
      const existingBookings = await this.bookingRepo.count({
        where: {
          providerId: dto.providerId,
          date: dto.date,
          timeSlot: dto.timeSlot,
          status: BookingStatus.CONFIRMED,
        },
      });

      if (existingBookings >= schedule.maxConcurrentBookings) {
        throw new BadRequestException('This time slot is fully booked.');
      }

      // 4. Calculate estimated price
      const estimatedPrice = await this.calculateServicePrice(
        dto.providerId,
        dto.serviceIds,
        dto.vehicleId,
      );

      // 5. Create booking
      const booking = this.bookingRepo.create({
        customerId,
        providerId: dto.providerId,
        vehicleId: dto.vehicleId,
        serviceIds: dto.serviceIds,
        date: dto.date,
        timeSlot: dto.timeSlot,
        estimatedPrice,
        customerNote: dto.note,
        status: BookingStatus.PENDING,
      });

      const saved = await this.bookingRepo.save(booking);

      // 6. Send notifications
      await Promise.all([
        this.notificationService.send({
          userId: dto.providerId,
          type: 'NEW_BOOKING',
          title: 'Lịch hẹn mới',
          body: `Khách hàng đã đặt lịch ${dto.serviceIds.join(', ')} vào ${dto.date} ${dto.timeSlot}`,
          data: { bookingId: saved.id },
        }),
        this.notificationService.send({
          userId: customerId,
          type: 'BOOKING_CONFIRMED',
          title: 'Đặt lịch thành công',
          body: `Lịch hẹn của bạn đã được ghi nhận. Vui lòng chờ xác nhận từ cửa hàng.`,
          data: { bookingId: saved.id },
        }),
      ]);

      // 7. Invalidate provider availability cache
      await this.redis.del(`provider:availability:${dto.providerId}:${dto.date}`);

      return saved;
    } finally {
      await this.redis.releaseLock(lockKey);
    }
  }

  async getProviderAvailability(
    providerId: string,
    date: string,
  ): Promise<TimeSlotAvailability[]> {
    const cacheKey = `provider:availability:${providerId}:${date}`;
    const cached = await this.redis.get(cacheKey);
    if (cached) return JSON.parse(cached);

    const dayOfWeek = new Date(date).getDay();
    
    // Get provider schedule for this day
    const schedule = await this.scheduleRepo.findOne({
      where: { providerId, dayOfWeek, isActive: true },
    });

    if (!schedule) return [];

    // Generate time slots
    const slots = this.generateTimeSlots(
      schedule.openTime,   // e.g., "08:00"
      schedule.closeTime,  // e.g., "18:00"
      schedule.slotDuration, // e.g., 60 (minutes)
    );

    // Get existing bookings
    const bookings = await this.bookingRepo.find({
      where: {
        providerId,
        date,
        status: BookingStatus.CONFIRMED,
      },
    });

    // Calculate availability
    const availability = slots.map(slot => {
      const booked = bookings.filter(b => b.timeSlot === slot).length;
      return {
        time: slot,
        available: booked < schedule.maxConcurrentBookings,
        remaining: schedule.maxConcurrentBookings - booked,
        total: schedule.maxConcurrentBookings,
      };
    });

    // Cache for 5 minutes
    await this.redis.set(cacheKey, JSON.stringify(availability), 300);
    return availability;
  }

  async updateBookingStatus(
    bookingId: string,
    status: BookingStatus,
    actorId: string,
    note?: string,
  ): Promise<Booking> {
    const booking = await this.bookingRepo.findOneOrFail({ 
      where: { id: bookingId },
      relations: ['customer', 'provider'],
    });

    // Validate state transition
    const validTransitions: Record<BookingStatus, BookingStatus[]> = {
      [BookingStatus.PENDING]: [BookingStatus.CONFIRMED, BookingStatus.CANCELLED],
      [BookingStatus.CONFIRMED]: [BookingStatus.IN_PROGRESS, BookingStatus.CANCELLED],
      [BookingStatus.IN_PROGRESS]: [BookingStatus.COMPLETED],
      [BookingStatus.COMPLETED]: [],
      [BookingStatus.CANCELLED]: [],
    };

    if (!validTransitions[booking.status]?.includes(status)) {
      throw new BadRequestException(
        `Cannot transition from ${booking.status} to ${status}`
      );
    }

    booking.status = status;
    booking.statusHistory = [
      ...(booking.statusHistory || []),
      { status, updatedBy: actorId, note, timestamp: new Date() },
    ];

    const updated = await this.bookingRepo.save(booking);

    // Trigger appropriate notifications
    await this._sendStatusNotification(updated);

    return updated;
  }
}
```

---

### 3.4. Personal Profile — Digital Twin Garage

```typescript
// backend/src/modules/vehicle/entities/vehicle.entity.ts
import { Entity, Column, PrimaryGeneratedColumn, ManyToOne, OneToMany } from 'typeorm';

@Entity('vehicles')
export class Vehicle {
  @PrimaryGeneratedColumn('uuid')
  id: string;

  @Column()
  ownerId: string;

  // Core specs
  @Column()
  make: string; // Toyota, Honda, etc.

  @Column()
  model: string; // Camry, Civic, etc.

  @Column()
  year: number;

  @Column({ nullable: true })
  trim: string; // 2.5Q, RS, etc.

  @Column({ unique: true })
  licensePlate: string;

  @Column({ nullable: true })
  vin: string; // Vehicle Identification Number

  @Column({ nullable: true })
  engineType: string; // Gasoline, Diesel, Hybrid, EV

  @Column({ nullable: true })
  transmission: string; // Manual, Automatic, CVT

  @Column({ type: 'decimal', nullable: true })
  engineDisplacement: number; // in liters

  @Column({ nullable: true })
  color: string;

  // Current status
  @Column({ type: 'int', default: 0 })
  currentMileage: number;

  @Column({ type: 'jsonb', nullable: true })
  lastServiceRecord: {
    date: string;
    mileage: number;
    serviceType: string;
    provider: string;
  };

  // Important dates
  @Column({ type: 'date', nullable: true })
  registrationExpiryDate: Date; // Đăng kiểm

  @Column({ type: 'date', nullable: true })
  insuranceExpiryDate: Date;

  @Column({ type: 'date', nullable: true })
  purchaseDate: Date;

  // Media
  @Column('text', { array: true, default: '{}' })
  photos: string[];

  // Service history (denormalized for quick access)
  @Column({ type: 'jsonb', default: '[]' })
  maintenanceTimeline: MaintenanceRecord[];

  // AI-generated health score
  @Column({ type: 'decimal', nullable: true })
  healthScore: number; // 0-100

  @Column({ type: 'jsonb', nullable: true })
  healthBreakdown: {
    engine: number;
    brakes: number;
    tires: number;
    fluids: number;
    electrical: number;
    body: number;
  };

  @Column({ type: 'jsonb', default: '[]' })
  upcomingMaintenanceAlerts: MaintenanceAlert[];

  @CreateDateColumn()
  createdAt: Date;

  @UpdateDateColumn()
  updatedAt: Date;
}

interface MaintenanceRecord {
  id: string;
  date: string;
  mileage: number;
  serviceType: 'oil_change' | 'tire_rotation' | 'brake_service' | 'inspection' | 'repair' | 'wash' | 'other';
  description: string;
  cost: number;
  providerId?: string;
  providerName: string;
  parts?: { name: string; quantity: number; price: number }[];
  documents?: string[]; // URLs to invoices/receipts
  bookingId?: string;
}

interface MaintenanceAlert {
  type: 'registration_expiry' | 'insurance_expiry' | 'mileage_service' | 'time_service' | 'recall';
  title: string;
  description: string;
  dueDate?: string;
  dueMileage?: number;
  urgency: 'low' | 'medium' | 'high' | 'critical';
  actionUrl?: string;
}
```

#### Vehicle Health Score AI

```python
# services/ai-engine/vehicle_health.py

class VehicleHealthAnalyzer:
    """
    Computes a 0-100 health score for a vehicle based on:
    - Age of the vehicle
    - Current mileage vs expected
    - Maintenance regularity
    - Last service dates
    - Known issues for make/model/year
    """
    
    async def compute_health_score(self, vehicle: dict) -> dict:
        age_years = (datetime.now() - datetime.fromisoformat(vehicle['purchase_date'])).days / 365
        
        scores = {}
        
        # Engine health (based on oil change frequency)
        oil_changes = [r for r in vehicle['maintenance_timeline'] if r['service_type'] == 'oil_change']
        if oil_changes:
            last_oil = datetime.fromisoformat(oil_changes[-1]['date'])
            days_since_oil = (datetime.now() - last_oil).days
            km_since_oil = vehicle['current_mileage'] - oil_changes[-1]['mileage']
            
            # Ideal: every 5000km or 6 months
            oil_score = 100
            if km_since_oil > 7500 or days_since_oil > 270:
                oil_score = 40  # Critical
            elif km_since_oil > 5000 or days_since_oil > 180:
                oil_score = 65  # Warning
            elif km_since_oil > 3000 or days_since_oil > 120:
                oil_score = 85  # Good
            scores['engine'] = oil_score
        else:
            scores['engine'] = 50  # Unknown
        
        # Brake health
        brake_services = [r for r in vehicle['maintenance_timeline'] if 'brake' in r['service_type']]
        if brake_services:
            km_since_brake = vehicle['current_mileage'] - brake_services[-1]['mileage']
            scores['brakes'] = max(20, 100 - (km_since_brake / 30000) * 100)
        else:
            scores['brakes'] = max(20, 100 - (vehicle['current_mileage'] / 40000) * 100)
        
        # Tire health (every 40,000 km rotation, 60,000 km replacement)
        tire_services = [r for r in vehicle['maintenance_timeline'] if 'tire' in r['service_type']]
        if tire_services:
            km_since_tire = vehicle['current_mileage'] - tire_services[-1]['mileage']
            scores['tires'] = max(20, 100 - (km_since_tire / 60000) * 100)
        else:
            scores['tires'] = max(20, 100 - (vehicle['current_mileage'] / 50000) * 100)
        
        # Overall maintenance regularity
        if len(vehicle['maintenance_timeline']) > 2:
            intervals = []
            sorted_records = sorted(vehicle['maintenance_timeline'], key=lambda x: x['date'])
            for i in range(1, len(sorted_records)):
                delta = (datetime.fromisoformat(sorted_records[i]['date']) - 
                        datetime.fromisoformat(sorted_records[i-1]['date'])).days
                intervals.append(delta)
            
            avg_interval = np.mean(intervals)
            regularity = min(100, max(40, 100 - abs(avg_interval - 90) * 0.5))
            scores['fluids'] = regularity
        else:
            scores['fluids'] = 60
        
        # Electrical & Body (simplified for MVP — use age/mileage proxy)
        scores['electrical'] = max(40, 100 - age_years * 5 - vehicle['current_mileage'] / 20000)
        scores['body'] = max(50, 100 - age_years * 3)
        
        # Weighted overall
        weights = {
            'engine': 0.30, 'brakes': 0.20, 'tires': 0.15,
            'fluids': 0.15, 'electrical': 0.10, 'body': 0.10
        }
        
        overall = sum(scores[k] * weights[k] for k in weights)
        
        # Generate alerts
        alerts = await self._generate_alerts(vehicle, scores)
        
        return {
            'overall_score': round(overall, 1),
            'breakdown': {k: round(v, 1) for k, v in scores.items()},
            'alerts': alerts,
            'computed_at': datetime.now().isoformat(),
        }
    
    async def _generate_alerts(self, vehicle: dict, scores: dict) -> list:
        alerts = []
        
        # Registration expiry check
        if vehicle.get('registration_expiry_date'):
            expiry = datetime.fromisoformat(vehicle['registration_expiry_date'])
            days_until = (expiry - datetime.now()).days
            if days_until <= 30:
                alerts.append({
                    'type': 'registration_expiry',
                    'title': 'Đăng kiểm sắp hết hạn',
                    'description': f'Xe cần đăng kiểm trong {days_until} ngày (hạn: {expiry.strftime("%d/%m/%Y")})',
                    'due_date': expiry.isoformat(),
                    'urgency': 'critical' if days_until <= 7 else 'high',
                })
        
        # Insurance expiry
        if vehicle.get('insurance_expiry_date'):
            expiry = datetime.fromisoformat(vehicle['insurance_expiry_date'])
            days_until = (expiry - datetime.now()).days
            if days_until <= 30:
                alerts.append({
                    'type': 'insurance_expiry',
                    'title': 'Bảo hiểm sắp hết hạn',
                    'description': f'Bảo hiểm xe hết hạn trong {days_until} ngày',
                    'due_date': expiry.isoformat(),
                    'urgency': 'high' if days_until <= 14 else 'medium',
                })
        
        # Component-level alerts
        for component, score in scores.items():
            if score < 50:
                alerts.append({
                    'type': 'mileage_service',
                    'title': f'Cần kiểm tra {component}',
                    'description': f'Điểm sức khỏe {component}: {score:.0f}/100. Nên đưa xe đi kiểm tra sớm.',
                    'urgency': 'critical' if score < 30 else 'high',
                })
        
        return sorted(alerts, key=lambda x: {'critical': 0, 'high': 1, 'medium': 2, 'low': 3}[x['urgency']])
```

---

### 3.5. Notification Center — Car Assistant

```typescript
// backend/src/modules/notification/notification.service.ts
import { Injectable } from '@nestjs/common';
import { Cron, CronExpression } from '@nestjs/schedule';
import * as firebase from 'firebase-admin';

@Injectable()
export class NotificationService {
  constructor(
    private readonly vehicleService: VehicleService,
    private readonly penaltyChecker: TrafficPenaltyService,
    private readonly pushService: PushNotificationService,
  ) {}

  // ==========================================
  // Scheduled Jobs
  // ==========================================

  @Cron(CronExpression.EVERY_DAY_AT_8AM)
  async dailyVehicleHealthCheck() {
    // Get all vehicles with upcoming maintenance needs
    const vehicles = await this.vehicleService.getVehiclesNeedingAttention();
    
    for (const vehicle of vehicles) {
      const alerts = vehicle.upcomingMaintenanceAlerts.filter(
        a => a.urgency === 'critical' || a.urgency === 'high'
      );
      
      if (alerts.length > 0) {
        await this.send({
          userId: vehicle.ownerId,
          type: 'MAINTENANCE_REMINDER',
          title: `⚠️ ${vehicle.make} ${vehicle.model} cần chú ý`,
          body: alerts[0].description,
          data: {
            vehicleId: vehicle.id,
            alertType: alerts[0].type,
          },
          channels: ['push', 'in_app'],
        });
      }
    }
  }

  @Cron('0 */6 * * *') // Every 6 hours
  async checkTrafficPenalties() {
    // Get all vehicles with license plates
    const vehicles = await this.vehicleService.getAllWithLicensePlates();
    
    for (const vehicle of vehicles) {
      try {
        const penalties = await this.penaltyChecker.check(vehicle.licensePlate);
        
        if (penalties.length > 0) {
          const newPenalties = await this._filterNewPenalties(vehicle.id, penalties);
          
          if (newPenalties.length > 0) {
            await this.send({
              userId: vehicle.ownerId,
              type: 'TRAFFIC_PENALTY',
              title: `🚨 Phát hiện ${newPenalties.length} phạt nguội mới`,
              body: `Biển số ${vehicle.licensePlate}: ${newPenalties[0].violation}`,
              data: {
                vehicleId: vehicle.id,
                penalties: newPenalties,
              },
              channels: ['push', 'in_app', 'email'],
              priority: 'high',
            });
          }
        }
      } catch (error) {
        // Log but don't crash the batch job
        this.logger.error(`Penalty check failed for ${vehicle.licensePlate}`, error);
      }
    }
  }

  @Cron(CronExpression.EVERY_DAY_AT_9AM)
  async registrationExpiryReminder() {
    // Find vehicles with registration expiring in 30, 14, 7, 3, 1 days
    const reminderDays = [30, 14, 7, 3, 1];
    
    for (const days of reminderDays) {
      const targetDate = new Date();
      targetDate.setDate(targetDate.getDate() + days);
      
      const vehicles = await this.vehicleService.findByRegistrationExpiry(targetDate);
      
      for (const vehicle of vehicles) {
        await this.send({
          userId: vehicle.ownerId,
          type: 'REGISTRATION_EXPIRY',
          title: `📋 Đăng kiểm còn ${days} ngày`,
          body: `${vehicle.make} ${vehicle.model} (${vehicle.licensePlate}) cần đăng kiểm trước ${targetDate.toLocaleDateString('vi-VN')}`,
          data: { vehicleId: vehicle.id, daysRemaining: days },
          channels: days <= 7 ? ['push', 'in_app', 'sms'] : ['push', 'in_app'],
          priority: days <= 3 ? 'high' : 'normal',
        });
      }
    }
  }

  // ==========================================
  // Core Send Method
  // ==========================================
  
  async send(notification: NotificationPayload): Promise<void> {
    // Save to database (in-app notification)
    const saved = await this.notificationRepo.save({
      userId: notification.userId,
      type: notification.type,
      title: notification.title,
      body: notification.body,
      data: notification.data,
      isRead: false,
    });

    // Send push notification
    if (notification.channels?.includes('push')) {
      const tokens = await this.getDeviceTokens(notification.userId);
      if (tokens.length > 0) {
        await this.pushService.sendMulticast({
          tokens,
          notification: {
            title: notification.title,
            body: notification.body,
          },
          data: {
            notificationId: saved.id,
            type: notification.type,
            ...notification.data,
          },
          android: {
            priority: notification.priority === 'high' ? 'high' : 'normal',
          },
          apns: {
            payload: {
              aps: {
                sound: notification.priority === 'high' ? 'critical.aiff' : 'default',
                badge: await this.getUnreadCount(notification.userId),
              },
            },
          },
        });
      }
    }

    // Real-time WebSocket notification
    this.wsGateway.sendToUser(notification.userId, 'notification', {
      id: saved.id,
      ...notification,
    });
  }
}
```

#### Traffic Penalty Checker

```typescript
// backend/src/modules/notification/traffic-penalty.service.ts
@Injectable()
export class TrafficPenaltyService {
  /**
   * Integrates with Vietnam traffic penalty lookup APIs
   * Source: csgt.vn / phatnguoi.vn (public API)
   */
  
  async check(licensePlate: string): Promise<TrafficPenalty[]> {
    const normalizedPlate = this.normalizePlate(licensePlate);
    
    // Check cache first (penalties don't change that frequently)
    const cached = await this.redis.get(`penalty:${normalizedPlate}`);
    if (cached) return JSON.parse(cached);
    
    try {
      // Call external API
      const response = await this.httpService.axiosRef.post(
        'https://api.checkphatnguoi.vn/phatnguoi',
        { bienso: normalizedPlate },
        { 
          timeout: 10000,
          headers: { 'X-API-Key': this.configService.get('PENALTY_API_KEY') }
        }
      );
      
      const penalties: TrafficPenalty[] = response.data.data.map(item => ({
        id: item.id,
        licensePlate: normalizedPlate,
        violation: item.loi_vi_pham,
        location: item.dia_diem,
        date: item.thoi_gian,
        fineAmount: item.so_tien,
        status: item.trang_thai, // 'unpaid' | 'paid'
        resolutionLocation: item.noi_giai_quyet,
      }));
      
      // Cache for 6 hours
      await this.redis.set(`penalty:${normalizedPlate}`, JSON.stringify(penalties), 21600);
      
      return penalties;
    } catch (error) {
      this.logger.error(`Failed to check penalties for ${normalizedPlate}`, error);
      return [];
    }
  }
  
  private normalizePlate(plate: string): string {
    return plate.replace(/[\s.-]/g, '').toUpperCase();
  }
}
```

---

### 3.6. Automatic Car Washing — Extension Feature

```typescript
// backend/src/modules/car-wash/car-wash.service.ts
@Injectable()
export class CarWashService {
  /**
   * Touchless car wash station integration
   * 
   * International models studied:
   * - WashTec (Germany): Sensor-guided, water recycling
   * - ISTOBAL (Spain): Connected platform, remote monitoring
   * - PDQ (USA): Pay-per-wash, membership models
   * 
   * Vietnam adaptation:
   * - QR code activation (no app download required for walk-ins)
   * - VNPay/MoMo/ZaloPay integration
   * - Water recycling compliance with local regulations
   */

  async findNearestStations(
    lat: number,
    lng: number,
    radius: number = 5000, // meters
    filters?: WashStationFilters,
  ): Promise<WashStation[]> {
    const query = `
      SELECT 
        ws.*,
        ST_Distance(
          ws.location::geography,
          ST_SetSRID(ST_MakePoint($1, $2), 4326)::geography
        ) as distance_meters,
        ws.current_queue_length,
        ws.estimated_wait_minutes,
        ws.pricing
      FROM wash_stations ws
      WHERE ST_DWithin(
        ws.location::geography,
        ST_SetSRID(ST_MakePoint($1, $2), 4326)::geography,
        $3
      )
      AND ws.status = 'operational'
      ${filters?.washType ? `AND ws.wash_type = '${filters.washType}'` : ''}
      ${filters?.maxPrice ? `AND (ws.pricing->>'basic')::decimal <= ${filters.maxPrice}` : ''}
      ORDER BY distance_meters ASC
      LIMIT 20
    `;

    const stations = await this.db.query(query, [lng, lat, radius]);

    return stations.map(s => ({
      ...s,
      distanceFormatted: s.distance_meters < 1000 
        ? `${Math.round(s.distance_meters)}m` 
        : `${(s.distance_meters / 1000).toFixed(1)}km`,
      estimatedArrival: this.calculateETA(s.distance_meters),
      services: [
        { name: 'Rửa cơ bản', price: s.pricing.basic, duration: '8 phút' },
        { name: 'Rửa cao cấp', price: s.pricing.premium, duration: '12 phút' },
        { name: 'Rửa VIP + Sáp', price: s.pricing.vip, duration: '18 phút' },
      ],
    }));
  }

  async initiateWashSession(dto: InitiateWashDto): Promise<WashSession> {
    // 1. Verify station availability
    const station = await this.getStationRealTimeStatus(dto.stationId);
    if (station.currentStatus !== 'available') {
      throw new BadRequestException(
        `Station is ${station.currentStatus}. Estimated wait: ${station.estimatedWaitMinutes} minutes`
      );
    }

    // 2. Create payment intent
    const payment = await this.paymentService.createIntent({
      amount: dto.washPackagePrice,
      method: dto.paymentMethod, // 'vnpay' | 'momo' | 'zalopay' | 'wallet'
      description: `Rửa xe ${dto.washPackage} - Trạm ${station.name}`,
      metadata: { stationId: dto.stationId, vehicleId: dto.vehicleId },
    });

    // 3. Create wash session
    const session = await this.washSessionRepo.save({
      stationId: dto.stationId,
      customerId: dto.customerId,
      vehicleId: dto.vehicleId,
      washPackage: dto.washPackage,
      paymentIntentId: payment.id,
      status: 'awaiting_payment',
      qrCode: await this.generateActivationQR(payment.id), // QR for station scanner
    });

    return session;
  }

  async confirmPaymentAndActivate(paymentId: string): Promise<void> {
    // Called by payment webhook
    const session = await this.washSessionRepo.findOne({
      where: { paymentIntentId: paymentId },
    });

    if (!session) throw new NotFoundException('Session not found');

    // Send activation command to IoT station
    await this.iotBridge.sendCommand(session.stationId, {
      action: 'START_WASH',
      program: session.washPackage,
      sessionId: session.id,
    });

    session.status = 'in_progress';
    session.startedAt = new Date();
    await this.washSessionRepo.save(session);

    // Notify customer
    await this.notificationService.send({
      userId: session.customerId,
      type: 'WASH_STARTED',
      title: '🚿 Rửa xe bắt đầu!',
      body: `Chương trình ${session.washPackage} đang chạy. Dự kiến hoàn thành trong vài phút.`,
    });
  }
}
```

---

## IV. Authentication & User Management

```typescript
// backend/src/modules/auth/auth.service.ts
@Injectable()
export class AuthService {
  async register(dto: RegisterDto): Promise<AuthResponse> {
    // Support both phone (OTP) and email registration
    const user = await this.userRepo.save({
      phone: dto.phone,
      email: dto.email,
      fullName: dto.fullName,
      role: dto.role, // 'customer' | 'provider'
      passwordHash: dto.password ? await bcrypt.hash(dto.password, 12) : null,
      authMethod: dto.phone ? 'phone_otp' : 'email_password',
    });

    // If provider, create provider profile
    if (dto.role === 'provider') {
      await this.providerRepo.save({
        userId: user.id,
        businessName: dto.businessName,
        businessType: dto.businessType, // 'garage' | 'car_care' | 'parts_retailer'
        address: dto.address,
        location: dto.location, // {lat, lng}
        verificationStatus: 'pending', // requires admin approval
      });
    }

    const tokens = await this.generateTokens(user);
    return { user: this.sanitize(user), ...tokens };
  }

  async loginWithOTP(phone: string): Promise<{ sessionId: string }> {
    // Rate limit: max 3 OTP requests per phone per hour
    const rateLimitKey = `otp:limit:${phone}`;
    const attempts = await this.redis.incr(rateLimitKey);
    if (attempts === 1) await this.redis.expire(rateLimitKey, 3600);
    if (attempts > 3) throw new TooManyRequestsException('Too many OTP requests');

    const otp = this.generateOTP(); // 6-digit
    const sessionId = uuidv4();

    // Store OTP with 5-minute TTL
    await this.redis.set(
      `otp:${sessionId}`,
      JSON.stringify({ phone, otp, attempts: 0 }),
      300
    );

    // Send OTP via SMS (SpeedSMS / Twilio)
    await this.smsService.send(phone, `Ma xac nhan AutoHub: ${otp}. Het han sau 5 phut.`);

    return { sessionId };
  }

  async verifyOTP(sessionId: string, otp: string): Promise<AuthResponse> {
    const data = await this.redis.get(`otp:${sessionId}`);
    if (!data) throw new UnauthorizedException('OTP expired');

    const { phone, otp: storedOtp, attempts } = JSON.parse(data);
    
    if (attempts >= 5) {
      await this.redis.del(`otp:${sessionId}`);
      throw new UnauthorizedException('Too many failed attempts');
    }

    if (otp !== storedOtp) {
      await this.redis.set(
        `otp:${sessionId}`,
        JSON.stringify({ phone, otp: storedOtp, attempts: attempts + 1 }),
        300
      );
      throw new UnauthorizedException('Invalid OTP');
    }

    await this.redis.del(`otp:${sessionId}`);

    // Find or create user
    let user = await this.userRepo.findOne({ where: { phone } });
    if (!user) {
      user = await this.userRepo.save({
        phone,
        authMethod: 'phone_otp',
        role: 'customer',
        isPhoneVerified: true,
      });
    }

    const tokens = await this.generateTokens(user);
    return { user: this.sanitize(user), ...tokens };
  }
}
```

---

## V. Mô Hình Kinh Doanh (Business Model)

### 5.1. Revenue Streams

```
┌──────────────────────────────────────────────────────────────────┐
│                    REVENUE MODEL OVERVIEW                         │
├──────────────────────┬───────────────────────┬───────────────────┤
│      Stream          │    Model              │  Target % Revenue │
├──────────────────────┼───────────────────────┼───────────────────┤
│ 1. Marketplace       │ Commission 5-15%      │      35%          │
│    Commission        │ per transaction       │                   │
├──────────────────────┼───────────────────────┼───────────────────┤
│ 2. Provider          │ Freemium + Tiered     │      25%          │
│    Subscription      │ Monthly/Annual        │                   │
├──────────────────────┼───────────────────────┼───────────────────┤
│ 3. Advertising &     │ CPM/CPC + Featured    │      20%          │
│    Promoted Content  │ listings              │                   │
├──────────────────────┼───────────────────────┼───────────────────┤
│ 4. Customer Premium  │ "AutoHub Pro" sub     │      10%          │
│    Subscription      │ Monthly/Annual        │                   │
├──────────────────────┼───────────────────────┼───────────────────┤
│ 5. Data & Insights   │ B2B analytics         │       5%          │
│    (Phase 2)         │ packages              │                   │
├──────────────────────┼───────────────────────┼───────────────────┤
│ 6. Car Wash          │ Revenue share         │       5%          │
│    Operations        │ 20-30% per wash       │                   │
└──────────────────────┴───────────────────────┴───────────────────┘
```

#### Detailed Pricing

**Provider Subscription Tiers:**

| Tier | Monthly Price | Features |
|------|:------------:|----------|
| **Starter** (Free) | 0 VND | Basic listing, 5 products, receive bookings, standard support |
| **Professional** | 499,000 VND (~$20) | Unlimited products, analytics dashboard, priority in search, CRM tools, booking calendar, 5% commission rate |
| **Enterprise** | 1,999,000 VND (~$80) | Multi-location, advanced analytics, API access, dedicated account manager, 3% commission rate, promoted placement |

**Customer Premium ("AutoHub Pro"):**

| | Free | Pro (99,000 VND/month) |
|---|:---:|:---:|
| Vehicle management | 1 vehicle | Unlimited |
| Health score | Basic | Detailed + AI predictions |
| Penalty check | Manual | Auto (every 6h) + alerts |
| Maintenance reminders | Basic | Smart + predictive |
| Marketplace discounts | — | 5-10% exclusive deals |
| Priority support | — | ✓ |
| Ad-free experience | — | ✓ |

**Marketplace Commission Structure:**

| Category | Commission Rate |
|----------|:--------------:|
| Phụ tùng thay thế | 8-12% |
| Phụ kiện & Đồ chơi | 10-15% |
| Dầu nhớt & Chất lỏng | 5-8% |
| Dịch vụ booking | 10-15% |
| Rửa xe (wash stations) | 20-30% |

### 5.2. Unit Economics (Year 1 Target)

```
Key Metrics (Month 12 Projection):
─────────────────────────────────────
Customers (MAU):           50,000
  ├── Free:                45,000
  └── Pro subscribers:      5,000 (10% conversion)
  
Providers:                  1,000
  ├── Starter (Free):        600
  ├── Professional:          300
  └── Enterprise:            100

Monthly Revenue Breakdown:
─────────────────────────────────────
Provider Subscriptions:
  300 × 499,000 + 100 × 1,999,000 = 349,600,000 VND

Customer Subscriptions:
  5,000 × 99,000 = 495,000,000 VND

Marketplace Commissions:
  Assume 10,000 transactions × avg 500,000 VND × 10% = 500,000,000 VND

Advertising:
  CPM-based + featured listings = 200,000,000 VND

Car Wash Revenue Share:
  2,000 washes × avg 150,000 VND × 25% = 75,000,000 VND
─────────────────────────────────────
Total Monthly Revenue (M12): ~1,620,000,000 VND (~$65,000/month)
Total Annual Revenue:        ~$500,000 (break-even with prize)

Customer Acquisition Cost (CAC): ~$2-5
Customer Lifetime Value (LTV): ~$50-100 (24-month horizon)
LTV/CAC Ratio: 10-50x ✓
```

---

## VI. Scalability Plan

### 6.1. Technical Scalability

```
Phase 1 (MVP - Months 1-6):
├── Monolithic NestJS → Deploy on AWS ECS (2-4 instances)
├── Single PostgreSQL RDS (db.r6g.large)
├── Redis ElastiCache (single node)
├── AI Engine: Single FastAPI instance + OpenAI API calls
└── Target: 10K MAU, <500ms p95 latency

Phase 2 (Growth - Months 6-18):
├── Extract microservices: Feed, Marketplace, Booking, Notification
├── PostgreSQL read replicas (1 writer + 2 readers)
├── Redis Cluster (3 nodes)
├── Elasticsearch cluster for search
├── AI Engine: GPU instance for local model inference
├── RabbitMQ → Kafka for event streaming
├── CDN (CloudFront) for static assets
└── Target: 100K MAU, <300ms p95 latency

Phase 3 (Scale - Months 18-36):
├── Kubernetes (EKS) for container orchestration
├── Database sharding by region (North/Central/South VN)
├── Dedicated ML pipeline (SageMaker/Vertex AI)
├── Real-time analytics (Apache Flink)
├── Multi-region deployment (VN → SEA)
└── Target: 1M+ MAU, <200ms p95 latency
```

### 6.2. Product Scalability — Vehicle Type Expansion

```
Phase 1 (MVP):     🚗 Ô tô (Cars)
Phase 2 (Month 9):  🏍️ Xe máy (Motorcycles) — 45M+ units in Vietnam
Phase 3 (Month 15): 🚚 Xe thương mại (Commercial vehicles — trucks, buses)
Phase 4 (Month 24): 🛵 Xe điện (EVs) — with charging station network
Phase 5 (Month 30): 🚜 Xe chuyên dụng (Specialized vehicles)
```

**Xe máy expansion** alone would 10x the addressable market in Vietnam (45M motorcycles vs 5M cars).

### 6.3. IoT Integration Roadmap

```
┌───────────────────────────────────────────────────────────────┐
│                    IoT DATA PIPELINE                          │
│                                                               │
│  OBD-II Dongle ──→ Bluetooth ──→ Mobile App ──→ AutoHub API  │
│  (ELM327/Custom)                                              │
│                                                               │
│  Data Collected:                                              │
│  ├── Engine RPM, Coolant Temp, Battery Voltage               │
│  ├── Fuel consumption (real-time MPG)                        │
│  ├── DTC (Diagnostic Trouble Codes)                          │
│  ├── Odometer reading (auto-update mileage)                  │
│  ├── GPS location + driving behavior                         │
│  └── Emission data                                           │
│                                                               │
│  AI Processing:                                               │
│  ├── Predictive maintenance (ML on sensor trends)            │
│  ├── Driving score (insurance partnership)                   │
│  ├── Fuel efficiency optimization                            │
│  └── Real-time DTC translation & severity assessment         │
└───────────────────────────────────────────────────────────────┘
```

**Partnership strategy:** Partner with OBD-II dongle manufacturers (e.g., Carista, FIXD) to offer co-branded "AutoHub Smart Dongle" at subsidized prices ($15-25), creating a hardware + software flywheel.

### 6.4. Geographic Expansion

```
Year 1: Vietnam (Hanoi, HCMC, Da Nang)
Year 2: Thailand, Indonesia (largest SEA car markets)
Year 3: Philippines, Malaysia
Year 4: Pan-SEA coverage + potential India pilot
```

---

## VII. Go-to-Market Strategy

### 7.1. Phase 1: Supply-Side First (Month 1-3)

> **"Get the providers, users will follow."**

```
Strategy: Onboard 100 quality providers in Hanoi & HCMC

Tactics:
├── Direct Sales Team (3-5 people) visiting top-rated garages
├── Free onboarding + professional photography of their shop
├── Offer 6-month FREE Professional tier subscription
├── Import their existing Google/Facebook reviews
├── Help them digitize service menus & pricing
└── Exclusive "Founding Partner" badge (permanent SEO boost)

Target providers:
├── 30 garages (multi-brand repair)
├── 20 authorized service centers (Toyota, Honda, Hyundai, etc.)
├── 20 car care / detailing shops
├── 15 parts retailers
├── 10 car wash stations
└── 5 inspection centers
```

### 7.2. Phase 2: Demand Generation (Month 2-6)

```
Channel Strategy:
─────────────────────────────────────────────
1. Content Marketing (Primary — lowest CAC)
   ├── YouTube channel: "AutoHub Tips" — weekly car maintenance videos
   ├── TikTok: Short-form car tips, before/after repairs
   ├── Blog/SEO: "Bảng giá bảo dưỡng [Car Model] 2024"
   │   Target keywords with 10K-100K monthly search volume
   └── Estimated CAC: $0.5-1.5

2. Community Seeding
   ├── Partner with existing car communities on Facebook
   │   (Otofun, Otosaigon, các group xe theo hãng)
   ├── Invite top contributors as "AutoHub Experts"
   ├── Cross-post valuable content with attribution
   └── Estimated CAC: $0.2-0.5

3. Referral Program
   ├── Customer → Customer: Both get 50K VND wallet credit
   ├── Customer → Provider: Customer gets 100K VND, Provider gets free month Pro
   ├── Provider → Provider: Referring provider gets 30% of first subscription
   └── Estimated CAC: $2-3 (but high-quality users)

4. Strategic Partnerships
   ├── Insurance companies (auto insurance): Bundle AutoHub Pro
   ├── New car dealerships: Pre-install app on delivered vehicles
   ├── Banks (auto loan): Offer AutoHub as value-add for car loan customers
   └── Fuel stations (Petrolimex, Shell): Cross-promotion

5. Paid Acquisition (Month 4+, after product-market fit signals)
   ├── Google Ads: "Gara uy tín gần tôi", "Phụ tùng [Model]"
   ├── Facebook/Instagram: Targeted to car owner demographics
   ├── Zalo Ads: Vietnam-specific, high engagement
   └── Estimated CAC: $3-8
```

### 7.3. Phase 3: Viral Loops & Network Effects (Month 6+)

```
Built-in Viral Mechanics:
─────────────────────────────────────────────
1. "Digital Garage Card"
   └── Shareable vehicle profile card (like LinkedIn profile)
       Owners share their car's health score on social media

2. Provider Review System
   └── "Verified on AutoHub" badge for providers
       Providers promote their AutoHub profile to existing customers

3. Vehicle Transfer
   └── When selling a car, transfer complete maintenance history
       Buyer must join AutoHub to receive — organic user acquisition

4. Community Expert Program
   └── Top contributors get verified badges, priority support
       Incentivizes content creation → attracts more readers
```

### 7.4. Key Metrics Dashboard

```
North Star Metric: Monthly Active Vehicles (MAV)
  — Vehicles with at least 1 interaction (booking, post, or data update)

Supporting Metrics:
├── Acquisition
│   ├── New user signups (daily/weekly)
│   ├── Vehicle profiles created
│   ├── Provider applications
│   └── CAC by channel
│
├── Activation
│   ├── % users who add a vehicle within 24h
│   ├── % users who complete first booking within 7 days
│   └── % providers who list 3+ services within 7 days
│
├── Retention
│   ├── D1/D7/D30 retention rates
│   ├── Monthly active rate
│   └── Provider monthly active rate
│
├── Revenue
│   ├── MRR (Monthly Recurring Revenue)
│   ├── ARPU (Average Revenue Per User)
│   ├── GMV (Gross Merchandise Value)
│   └── Take rate (revenue / GMV)
│
└── Engagement
    ├── Posts per day
    ├── Bookings per provider per month
    ├── Feed engagement rate (likes+comments / impressions)
    └── NPS (Net Promoter Score)
```

---

## VIII. MVP Development Timeline

```
Week 1-2:  Project setup, DB schema, Auth system, basic API scaffold
Week 3-4:  Vehicle CRUD, User profiles, Provider onboarding
Week 5-6:  Social Feed (basic, without AI ranking)
Week 7-8:  Marketplace (product listing, search, cart, checkout)
Week 9-10: Booking system, Provider calendar
Week 11:   Notification center, scheduled jobs
Week 12:   AI integration (feed ranking, recommendations, health score)
Week 13:   Car wash feature (station finder, payment flow)
Week 14:   Mobile app polish, performance optimization
Week 15:   Testing, bug fixes, soft launch
Week 16:   Official launch 🚀
```

**Team Composition (MVP):**

| Role | Count | Focus |
|------|:-----:|-------|
| Full-stack Lead | 1 | Architecture, backend core |
| Backend Developer | 2 | Microservices, APIs, integrations |
| Mobile Developer | 2 | React Native (iOS + Android) |
| Frontend Developer | 1 | Web app + Provider dashboard |
| AI/ML Engineer | 1 | Recommendation, feed ranking, NLP |
| UI/UX Designer | 1 | Product design, user research |
| Product Manager | 1 | Roadmap, metrics, stakeholder |
| DevOps | 1 | Infrastructure, CI/CD, monitoring |
| **Total** | **10** | |

---

## IX. Competitive Moat & Differentiation

```
┌────────────────────────────────────────────────────────────────┐
│                    COMPETITIVE LANDSCAPE                        │
├──────────────────┬────────┬────────┬─────────┬────────────────┤
│     Feature      │AutoHub │Otofun  │Garage   │ Shopee/Lazada  │
│                  │(Ours)  │/Forums │Finders  │ (Parts)        │
├──────────────────┼────────┼────────┼─────────┼────────────────┤
│ Social Community │  ✅ AI │  ✅    │   ❌    │      ❌        │
│ Vehicle Profile  │  ✅    │  ❌    │   ❌    │      ❌        │
│ Service Booking  │  ✅    │  ❌    │   ✅    │      ❌        │
│ Parts Marketplace│  ✅    │  ❌    │   ❌    │      ✅        │
│ AI Recommender   │  ✅    │  ❌    │   ❌    │  Generic AI    │
│ Penalty Alerts   │  ✅    │  ❌    │   ❌    │      ❌        │
│ Maintenance Track│  ✅    │  ❌    │   ❌    │      ❌        │
│ Car Wash Booking │  ✅    │  ❌    │   ❌    │      ❌        │
│ Health Score     │  ✅    │  ❌    │   ❌    │      ❌        │
│ IoT Integration  │  🔜    │  ❌    │   ❌    │      ❌        │
|
├──────────────────┼────────┼────────┼─────────┼────────────────┤
│ ALL-IN-ONE       │  ✅    │  ❌    │   ❌    │      ❌        │
└──────────────────┴────────┴────────┴─────────┴────────────────┘

Key Moats:
1. DATA NETWORK EFFECT: More users → more vehicle data → better AI → 
   better recommendations → more users
   
2. SWITCHING COST: Once a user builds 2+ years of maintenance history,
   they won't leave (like switching banks)
   
3. TWO-SIDED MARKETPLACE: Providers depend on platform for bookings,
   customers depend on platform for trusted providers
   
4. AI FLYWHEEL: User interactions train the model → better UX → 
   more interactions → stronger AI
```

---

## X. Risk Mitigation

| Risk | Probability | Impact | Mitigation |
|------|:----------:|:------:|------------|
| Low initial provider adoption | Medium | High | Free tier + direct sales team + 6-month free Pro |
| Cold start problem (no content) | High | High | Seed content from existing forums (with permission) + hire 5 automotive experts to create initial content |
| Payment integration issues in VN | Medium | Medium | Start with VNPay (most stable) + add MoMo/ZaloPay incrementally |
| Penalty API reliability | High | Low | Multiple data sources + graceful degradation + cache |
| User data privacy concerns | Medium | High | SOC2 compliance roadmap, transparent data policy, user data export/delete |
| Competitor copying features | Medium | Medium | Speed of execution + data moat + brand building |

---

## XI. Hackathon Presentation Strategy

> **For the $500K hackathon, emphasize:**

1. **🎯 Problem Size:** 5M+ cars in Vietnam, 45M+ motorcycles. Fragmented service experience. No single platform owns the relationship.

2. **💡 Unique Insight:** The vehicle is the "account," not the person. Digital Twin Garage creates unprecedented lock-in and data value.

3. **📊 Business Viability:** Multiple revenue streams, strong unit economics (LTV/CAC > 10x), clear path to profitability within 18 months.

4. **🔧 Technical Demo:** Show working AI feed ranking, real-time booking flow, vehicle health score computation, and penalty checking — all live.

5. **📈 Scalability Story:** Cars → Motorcycles (10x market) → SEA expansion → IoT integration → Insurance/Finance partnerships.

6. **🏆 Traction Plan:** Day 1 actionable GTM with specific provider targets and content strategy already mapped.

---

## Appendix A — MVP Clean Architecture Plan (8 tuần)

Mục tiêu: Hoàn thiện phiên bản MVP trong 8 tuần (4 sprint, mỗi sprint 2 tuần) với kiến trúc Clean Architecture cho Backend (NestJS) và Frontend (Next.js & React Native), DB/external-agnostic qua Ports/Adapters.

Phạm vi MVP (4 tính năng cốt lõi)
- Digital Twin: Quản lý xe + Health Score cơ bản (rule-based, không phụ thuộc AI).
- Social Feed: Feed đơn giản, AI Ranking dùng Mock AI service.
- Booking: Đặt lịch gara (request → confirm → in-progress → done/cancel).
- Marketplace: Listing cơ bản + Checkout tối giản (mock payment adapter).

### 1) Folder Structure (Clean Architecture)

Backend (NestJS)
```
backend/
  src/
    domain/                    # Entities, ValueObjects, Domain services (pure TS)
    use-cases/                 # Application business rules (không phụ thuộc infra)
    controllers/               # HTTP controllers (Nest)
    dtos/                      # Request/Response DTOs + mappers
    ports/                     # Interfaces: repositories, external services
    infrastructure/            # Adapters triển khai ports
      persistence/
        typeorm/               # hoặc prisma/
      external/
        ai/                    # mock-ai.service.ts
        payment/               # stripe.adapter.ts (stub)
    shared/                    # errors, logger, utils
    main.ts
  test/
  package.json
```

Frontend Monorepo (Next.js + React Native)
```
frontend/
  apps/
    web/                       # Next.js
      src/
        domain/
        usecases/              # hooks/services gọi API theo use-case
        presentation/          # pages/, components/
        infrastructure/        # api client, storage adapters
    mobile/                    # React Native (Expo)
      src/
        domain/
        usecases/
        presentation/
        infrastructure/
  packages/
    shared-types/              # TS types chia sẻ backend/web/mobile
    api-client/                # typed fetchers / RTK Query hooks
    ui-kit/                    # shared UI components
  package.json (pnpm/yarn workspaces)
```

Nguyên tắc: Mọi truy cập DB/external đều qua `ports` và triển khai ở `infrastructure/*` để dễ mock/thay thế.

### 2) Domain Models (Entities chính — rút gọn)
- Vehicle: { id, ownerId, vin?, make, model, year, currentMileage, healthScore(0-100)?, healthBreakdown?, maintenanceTimeline[], upcomingMaintenanceAlerts[], createdAt, updatedAt }
- User: { id, name, email/phone, role: 'user'|'garage'|'admin', createdAt }
- Booking: { id, vehicleId, garageId, userId, scheduledAt, timeSlot?, status: requested|confirmed|in_progress|done|cancelled, services[{code, price}], createdAt }
- Listing: { id, sellerId, title, description, price{amount,currency}, images[], status: active|sold|removed, createdAt }
- FeedItem: { id, authorId, content, media[], likes, comments, aiScore?, createdAt }
- Order (Marketplace tối thiểu): { id, listingId, buyerId, amount, status: pending|paid|failed|refunded }

Value Objects: Money, TelemetrySnapshot, Coordinates.

### 3) Use Cases (hợp đồng rút gọn)
- CalculateVehicleHealth(input: {vehicleId | telemetry[]}) → {score, breakdown} | Errors: VehicleNotFound, InsufficientTelemetry
- UpdateVehicleTelemetry(input: {vehicleId, snapshot}) → Vehicle | Errors: VehicleNotFound, ValidationError
- CreateBooking(input: {userId, vehicleId, garageId, scheduledAt, services[]}) → {bookingId, status: requested}
- ConfirmBooking(input: {bookingId, garageId}) → {status: confirmed} | Errors: Unauthorized, BookingNotFound
- ListMarketplace(input: {filters, page, limit}) → {items[], total}
- CreateListing(input: {sellerId, data}) → {listingId}
- CheckoutListing(input: {buyerId, listingId, paymentMethod}) → {orderId, paymentStatus} | Errors: PaymentFailed, OutOfStock
- GetFeed(input: {userId, page, limit}) → {feedItems[]} (đã xếp hạng)
- CreateFeedItem(input: {authorId, content, media[]}) → {feedItemId}
- RankFeedItems(input: {items[], userContext}) → {itemsWithScores[]} — dùng `ai-ranking.port` (MVP: mock adapter)

Quy ước: Use-case thuần TS, chỉ phụ thuộc `ports`. Trả về Result<T,Error> hoặc throw domain errors; có thể dùng RxJS cho luồng telemetry.

### 4) Tech Stack Mapping (theo lớp)
Backend (NestJS)
- Domain/Use-cases: TypeScript thuần; RxJS (stream), nest DI cho wiring
- Controllers: @nestjs/common, routing, validation: class-validator + class-transformer
- Persistence (Infrastructure): TypeORM + PostgreSQL (pg) hoặc Prisma (tuỳ chọn)
- Migrations: TypeORM migrations hoặc Prisma migrate
- Docs: @nestjs/swagger; Testing: Jest + supertest; Logging: nestjs-pino
- Queue (tùy chọn): BullMQ + Redis cho tác vụ async
- AI Mock: mock-ai.service.ts triển khai `ai-ranking.port`
- Payment Adapter (mock): stripe-node (stub sau port `payment-gateway.port`)
- Auth: JWT (nestjs/passport, passport-jwt)

Frontend (Next.js & React Native)
- Data: React Query hoặc RTK Query; axios/fetch bọc trong `packages/api-client`
- Forms/validation: react-hook-form + zod; State: light (query cache + local state)
- UI: TailwindCSS (web), React Native Paper (mobile); Navigation: next/router, react-navigation
- Shared types: `packages/shared-types`; Testing: RTL + Jest
- Storage (mobile): AsyncStorage/MMKV

Dev tooling/Monorepo: pnpm workspaces hoặc Yarn; ESLint + Prettier + TS; GitHub Actions CI.

### 5) Roadmap 8 tuần (4 sprint × 2 tuần)
- Sprint 1 (Tuần 1–2): Skeleton + Digital Twin (Health)
  - Backend: Nest skeleton, Vehicle entity + repo port + TypeORM repo; CalculateVehicleHealth use-case (rule-based) + unit tests; VehicleController (create/get/update telemetry).
  - Frontend: Next.js + RN (Expo) skeleton; shared-types; màn Vehicles (list/detail) hiển thị health score.
  - KQ: CRUD vehicle + tính health end-to-end.

- Sprint 2 (Tuần 3–4): Booking
  - Backend: Booking entity + ports; Create/Confirm use-cases; controller + validation; e2e booking basic.
  - Frontend: luồng tạo/confirm booking; chọn xe/garage/thời gian.
  - KQ: Booking flow hoạt động, chặn trùng slot cơ bản.

- Sprint 3 (Tuần 5–6): Social Feed + Mock AI Ranking
  - Backend: FeedItem + repo; GetFeed/CreateFeed; `ai-ranking.port` + mock-ai.service; RankFeed use-case; GET /feed trả danh sách đã xếp hạng.
  - Frontend: UI feed (infinite scroll), tạo post đơn giản.
  - KQ: Feed sắp xếp ổn định theo mock rules.

- Sprint 4 (Tuần 7–8): Marketplace (Listing + Checkout) + Hardening
  - Backend: Listing create/list; CheckoutListing + Order (mock payment); đảm bảo đánh dấu sold (transactional guard).
  - Frontend: Browse listing, detail, checkout (mock payment UI).
  - Cross-cutting: JWT auth + RBAC cơ bản, Swagger, tăng test coverage, logs.
  - KQ: Hoàn tất 4 tính năng MVP, CI xanh.

Ghi chú kiểm thử & chất lượng
- Unit test cho mọi use-case (happy path + edge cases); e2e: vehicles, bookings, feed ranking, checkout.
- Lint/format/TypeCheck trong CI; yêu cầu coverage ~70% cho domain/use-cases.

---

Next step gợi ý: khởi tạo skeleton monorepo (pnpm), tạo `packages/shared-types`, scaffold NestJS Module Vehicle + use-case `CalculateVehicleHealth`, và Next.js trang Vehicles. Nếu cần, tôi sẽ tạo các file khởi tạo ngay trong repo này.