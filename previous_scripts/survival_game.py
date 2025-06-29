import pygame
import random
import math
import sys

# Initialize Pygame
pygame.init()
pygame.mixer.init()

# Constants
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 700
FPS = 60

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
BLUE = (100, 150, 255)
GREEN = (100, 200, 100)
BROWN = (139, 69, 19)
GRAY = (128, 128, 128)
RED = (255, 100, 100)
YELLOW = (255, 255, 100)
SKIN_COLOR = (255, 220, 177)

# Game settings
GRAVITY = 0.8
JUMP_STRENGTH = -15
MOVE_SPEED = 5
INITIAL_STEP_SPEED = 1
MAX_STEP_SPEED = 4
STEP_SPAWN_RATE = 120
GRAB_DISTANCE = 45  # Increased for better grabbing

class Player:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.width = 25
        self.height = 45
        self.vel_x = 0
        self.vel_y = 0
        self.on_ground = False
        self.grabbing = False
        self.grab_step = None
        self.facing_right = True
        self.animation_frame = 0
        self.animation_timer = 0
        self.state = "idle"
        
    def update(self, steps):
        # Handle input
        keys = pygame.key.get_pressed()
        
        if not self.grabbing:
            # Horizontal movement
            if keys[pygame.K_LEFT]:
                self.vel_x = -MOVE_SPEED
                self.facing_right = False
                if self.on_ground:
                    self.state = "running"
            elif keys[pygame.K_RIGHT]:
                self.vel_x = MOVE_SPEED
                self.facing_right = True
                if self.on_ground:
                    self.state = "running"
            else:
                self.vel_x = 0
                if self.on_ground:
                    self.state = "idle"
            
            # Jumping
            if (keys[pygame.K_UP] or keys[pygame.K_SPACE]) and self.on_ground:
                self.vel_y = JUMP_STRENGTH
                self.on_ground = False
                self.state = "jumping"
                
        else:
            # Climbing logic
            if keys[pygame.K_UP]:
                return self.climb_onto_step()
        
        # Apply gravity
        if not self.grabbing:
            self.vel_y += GRAVITY
            
        # Update position
        if not self.grabbing:
            self.x += self.vel_x
            self.y += self.vel_y
            
        # Keep player on screen horizontally
        self.x = max(0, min(SCREEN_WIDTH - self.width, self.x))
        
        # Check collisions with steps
        landed_step = self.check_step_collisions(steps)
        
        # Check for grabbing opportunities
        if not self.on_ground and not self.grabbing:
            self.check_grab_opportunities(steps)
            
        # Update animations
        self.update_animation()
        
        return landed_step
        
    def check_step_collisions(self, steps):
        player_rect = pygame.Rect(self.x, self.y, self.width, self.height)
        self.on_ground = False
        
        for step in steps:
            step_rect = pygame.Rect(step.x, step.y, step.width, step.height)
            
            if player_rect.colliderect(step_rect) and self.vel_y >= 0:
                # Landing on top of step
                if self.y < step.y:
                    self.y = step.y - self.height
                    self.vel_y = 0
                    self.on_ground = True
                    self.state = "idle"
                    return step
        return None
    
    def check_grab_opportunities(self, steps):
        for step in steps:
            # Enhanced grab detection - more forgiving
            player_center_x = self.x + self.width / 2
            player_center_y = self.y + self.height / 2
            step_center_x = step.x + step.width / 2
            step_center_y = step.y + step.height / 2
            
            distance = math.sqrt((player_center_x - step_center_x)**2 + 
                               (player_center_y - step_center_y)**2)
            
            # More lenient grabbing conditions
            if (distance < GRAB_DISTANCE and 
                abs(player_center_y - step_center_y) < 35 and
                abs(player_center_x - step_center_x) < step.width/2 + 20):
                
                self.grab_step = step
                self.grabbing = True
                self.state = "grabbing"
                self.vel_x = 0
                self.vel_y = 0
                # Position player hanging from step
                self.x = step.x + step.width/2 - self.width/2
                self.y = step.y + step.height
                break
    
    def climb_onto_step(self):
        if self.grab_step:
            self.y = self.grab_step.y - self.height
            self.grabbing = False
            self.on_ground = True
            self.state = "idle"
            climbed_step = self.grab_step
            self.grab_step = None
            return climbed_step
        return None
    
    def update_animation(self):
        self.animation_timer += 1
        if self.animation_timer >= 8:
            self.animation_frame = (self.animation_frame + 1) % 4
            self.animation_timer = 0
    
    def draw(self, screen):
        # Human-like character sprite
        
        # Head
        head_x = self.x + self.width//2
        head_y = self.y + 8
        pygame.draw.circle(screen, SKIN_COLOR, (int(head_x), int(head_y)), 8)
        
        # Eyes
        eye_offset = 3 if self.facing_right else -3
        pygame.draw.circle(screen, BLACK, (int(head_x + eye_offset), int(head_y - 2)), 2)
        
        # Body
        body_color = GREEN
        if self.state == "jumping":
            body_color = YELLOW
        elif self.state == "grabbing":
            body_color = RED
        elif self.state == "running":
            body_color = BLUE
            
        pygame.draw.rect(screen, body_color, (self.x + 5, self.y + 16, self.width - 10, 20))
        
        # Arms
        arm_y = self.y + 20
        if self.state == "grabbing":
            # Arms reaching up
            pygame.draw.line(screen, SKIN_COLOR, (self.x + 8, arm_y), (self.x + 3, self.y + 5), 4)
            pygame.draw.line(screen, SKIN_COLOR, (self.x + self.width - 8, arm_y), 
                           (self.x + self.width - 3, self.y + 5), 4)
        elif self.state == "running":
            # Swinging arms
            arm_swing = math.sin(self.animation_frame * 0.8) * 8
            pygame.draw.line(screen, SKIN_COLOR, (self.x + 8, arm_y), 
                           (self.x + 8 + arm_swing, arm_y + 12), 4)
            pygame.draw.line(screen, SKIN_COLOR, (self.x + self.width - 8, arm_y), 
                           (self.x + self.width - 8 - arm_swing, arm_y + 12), 4)
        else:
            # Normal arms
            pygame.draw.line(screen, SKIN_COLOR, (self.x + 8, arm_y), (self.x + 8, arm_y + 12), 4)
            pygame.draw.line(screen, SKIN_COLOR, (self.x + self.width - 8, arm_y), 
                           (self.x + self.width - 8, arm_y + 12), 4)
        
        # Legs
        leg_y = self.y + 36
        if self.state == "running":
            # Running legs animation
            leg_swing = math.sin(self.animation_frame) * 10
            pygame.draw.line(screen, BLUE, (self.x + 8, leg_y), 
                           (self.x + 8 + leg_swing, leg_y + 15), 4)
            pygame.draw.line(screen, BLUE, (self.x + self.width - 8, leg_y), 
                           (self.x + self.width - 8 - leg_swing, leg_y + 15), 4)
        elif self.state == "jumping":
            # Bent legs for jumping
            pygame.draw.line(screen, BLUE, (self.x + 8, leg_y), (self.x + 12, leg_y + 10), 4)
            pygame.draw.line(screen, BLUE, (self.x + self.width - 8, leg_y), 
                           (self.x + self.width - 12, leg_y + 10), 4)
        else:
            # Standing legs
            pygame.draw.line(screen, BLUE, (self.x + 8, leg_y), (self.x + 8, leg_y + 15), 4)
            pygame.draw.line(screen, BLUE, (self.x + self.width - 8, leg_y), 
                           (self.x + self.width - 8, leg_y + 15), 4)

class Step:
    def __init__(self, x, y, width, column):
        self.x = x
        self.y = y
        self.width = width
        self.height = 20
        self.column = column
        self.color = BROWN
        
    def update(self, speed):
        self.y -= speed
        
    def draw(self, screen):
        pygame.draw.rect(screen, self.color, (self.x, self.y, self.width, self.height))
        pygame.draw.rect(screen, BLACK, (self.x, self.y, self.width, self.height), 2)

class StepGenerator:
    def __init__(self):
        self.spawn_timer = 0
        self.difficulty = 1.0
        
    def update(self, steps, game_time):
        # Progressive difficulty
        self.difficulty = 1 + (game_time / 10000)
        
        self.spawn_timer += 1
        spawn_rate = max(30, int(STEP_SPAWN_RATE / self.difficulty))
        
        if self.spawn_timer >= spawn_rate:
            self.spawn_step(steps, game_time)
            self.spawn_timer = 0
    
    def spawn_step(self, steps, game_time):
        # Choose random column
        column = random.randint(0, 2)
        
        # Progressive step difficulty - start with 90% easy steps
        time_factor = min(game_time / 15000, 1.0)  # Max difficulty after 4 minutes
        easy_probability = 0.9 - (0.4 * time_factor)  # Goes from 90% to 50%
        
        if random.random() < easy_probability:
            # Easy step (large)
            step_width = random.randint(120, 160)
        else:
            # Harder step (smaller)
            step_width = random.randint(60, 100)
        
        # Position based on column
        if column == 0:  # Left wall
            x = 50
        elif column == 1:  # Middle
            x = SCREEN_WIDTH // 2 - step_width // 2
        else:  # Right wall
            x = SCREEN_WIDTH - 50 - step_width
        
        y = SCREEN_HEIGHT + 20
        
        new_step = Step(x, y, step_width, column)
        steps.append(new_step)

class Plane:
    def __init__(self):
        self.x = -120
        self.y = 100
        self.width = 80
        self.height = 30
        self.speed = 2
        self.active = False
        
    def update(self):
        if self.active:
            self.x += self.speed
            
    def draw(self, screen):
        if self.active and self.x < SCREEN_WIDTH + 100:
            # Simple plane
            pygame.draw.ellipse(screen, GRAY, (self.x, self.y, self.width, self.height))
            pygame.draw.polygon(screen, GRAY, [
                (self.x + self.width, self.y + self.height//2),
                (self.x + self.width + 15, self.y + self.height//2 - 8),
                (self.x + self.width + 15, self.y + self.height//2 + 8)
            ])

class Game:
    def __init__(self):
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Survival Points Game")
        self.clock = pygame.time.Clock()
        self.running = True
        self.game_state = "start"  # start, intro, playing, game_over
        self.score = 0
        self.game_time = 0
        self.font = pygame.font.Font(None, 36)
        self.big_font = pygame.font.Font(None, 72)
        
        # Game objects
        self.player = None
        self.plane = Plane()
        self.steps = []
        self.step_generator = StepGenerator()
        self.step_speed = INITIAL_STEP_SPEED
        self.last_step_landed = None
        self.intro_timer = 0
        self.parachute_timer = 0
        
    def reset_game(self):
        self.player = None
        self.steps = []
        self.score = 0
        self.game_time = 0
        self.step_speed = INITIAL_STEP_SPEED
        self.step_generator = StepGenerator()
        self.last_step_landed = None
        self.intro_timer = 0
        self.parachute_timer = 0
        
        # Start intro sequence
        self.game_state = "intro"
        self.plane = Plane()
        self.plane.x = -120
        self.plane.active = True
        
        # Create initial step for landing
        initial_step = Step(SCREEN_WIDTH // 2 - 75, SCREEN_HEIGHT - 100, 150, 1)
        self.steps.append(initial_step)
    
    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.KEYDOWN:
                if self.game_state == "start" and event.key == pygame.K_SPACE:
                    self.reset_game()
                elif self.game_state == "game_over" and event.key == pygame.K_SPACE:
                    self.game_state = "start"
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if self.game_state == "start":
                    mouse_x, mouse_y = pygame.mouse.get_pos()
                    button_rect = pygame.Rect(SCREEN_WIDTH//2 - 100, SCREEN_HEIGHT//2, 200, 50)
                    if button_rect.collidepoint(mouse_x, mouse_y):
                        self.reset_game()
    
    def update(self):
        if self.game_state == "intro":
            self.intro_timer += 1
            self.plane.update()
            
            # Player jumps from plane
            if self.plane.x > SCREEN_WIDTH // 2 and not self.player:
                self.player = Player(self.plane.x + 40, self.plane.y + 30)
                self.player.vel_y = 2  # Slow fall
                self.parachute_timer = 120  # 2 seconds
            
            # Handle parachute landing
            if self.player:
                if self.parachute_timer > 0:
                    self.parachute_timer -= 1
                    self.player.y += 2  # Slow descent
                else:
                    # Switch to playing mode
                    self.game_state = "playing"
                    # Position player on initial step
                    for step in self.steps:
                        if step.y > SCREEN_HEIGHT - 150:
                            self.player.y = step.y - self.player.height
                            self.player.x = step.x + step.width/2 - self.player.width/2
                            self.player.on_ground = True
                            break
                
        elif self.game_state == "playing":
            self.game_time += 1
            
            # Update step speed
            self.step_speed = min(MAX_STEP_SPEED, INITIAL_STEP_SPEED + (self.game_time / 3000))
            
            # Update player
            landed_step = self.player.update(self.steps)
            if landed_step and landed_step != self.last_step_landed:
                self.score += 1
                self.last_step_landed = landed_step
            
            # Update steps
            for step in self.steps[:]:
                step.update(self.step_speed)
                if step.y < -step.height:
                    self.steps.remove(step)
            
            # Generate new steps
            self.step_generator.update(self.steps, self.game_time)
            
            # Check game over
            if self.player.y > SCREEN_HEIGHT:
                self.game_state = "game_over"
    
    def draw_start_screen(self):
        self.screen.fill(BLUE)
        
        # Title
        title_text = self.big_font.render("Survival Points", True, WHITE)
        title_rect = title_text.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2 - 100))
        self.screen.blit(title_text, title_rect)
        
        # Start button
        button_rect = pygame.Rect(SCREEN_WIDTH//2 - 100, SCREEN_HEIGHT//2, 200, 50)
        pygame.draw.rect(self.screen, GREEN, button_rect)
        pygame.draw.rect(self.screen, BLACK, button_rect, 3)
        
        button_text = self.font.render("Start Game", True, BLACK)
        button_text_rect = button_text.get_rect(center=button_rect.center)
        self.screen.blit(button_text, button_text_rect)
        
        # Instructions
        instructions = [
            "Use arrow keys to move and jump",
            "Get close to steps to grab them automatically",
            "Press UP to climb onto grabbed steps",
            "Game starts easy and gets progressively harder!"
        ]
        
        for i, instruction in enumerate(instructions):
            text = self.font.render(instruction, True, WHITE)
            text_rect = text.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2 + 100 + i * 30))
            self.screen.blit(text, text_rect)
    
    def draw_game_over_screen(self):
        self.screen.fill(RED)
        
        # Game Over text
        game_over_text = self.big_font.render("Game Over", True, WHITE)
        game_over_rect = game_over_text.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2 - 50))
        self.screen.blit(game_over_text, game_over_rect)
        
        # Final score
        score_text = self.font.render(f"Final Score: {self.score}", True, WHITE)
        score_rect = score_text.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2))
        self.screen.blit(score_text, score_rect)
        
        # Restart instruction
        restart_text = self.font.render("Press SPACE to return to menu", True, WHITE)
        restart_rect = restart_text.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2 + 50))
        self.screen.blit(restart_text, restart_rect)
    
    def draw_game(self):
        self.screen.fill(WHITE)
        
        # Draw walls
        pygame.draw.rect(self.screen, GRAY, (0, 0, 50, SCREEN_HEIGHT))
        pygame.draw.rect(self.screen, GRAY, (SCREEN_WIDTH - 50, 0, 50, SCREEN_HEIGHT))
        
        # Draw steps
        for step in self.steps:
            step.draw(self.screen)
        
        # Draw plane during intro
        if self.game_state == "intro":
            self.plane.draw(self.screen)
            
            # Draw parachute if player is falling
            if self.player and self.parachute_timer > 0:
                parachute_x = self.player.x + self.player.width//2
                parachute_y = self.player.y - 30
                pygame.draw.arc(self.screen, RED, (parachute_x - 20, parachute_y, 40, 25), 0, math.pi, 3)
                pygame.draw.line(self.screen, BLACK, (parachute_x - 15, parachute_y + 12), 
                               (self.player.x + 5, self.player.y), 2)
                pygame.draw.line(self.screen, BLACK, (parachute_x + 15, parachute_y + 12), 
                               (self.player.x + self.player.width - 5, self.player.y), 2)
        
        # Draw player
        if self.player:
            self.player.draw(self.screen)
        
        # Draw UI
        score_text = self.font.render(f"Score: {self.score}", True, BLACK)
        self.screen.blit(score_text, (10, 10))
        
        speed_text = self.font.render(f"Speed: {self.step_speed:.1f}", True, BLACK)
        self.screen.blit(speed_text, (10, 50))
        
        # Show grab instruction
        if self.player and self.player.grabbing:
            grab_text = self.font.render("Press UP to climb!", True, RED)
            grab_rect = grab_text.get_rect(center=(SCREEN_WIDTH//2, 100))
            self.screen.blit(grab_text, grab_rect)
    
    def draw(self):
        if self.game_state == "start":
            self.draw_start_screen()
        elif self.game_state in ["intro", "playing"]:
            self.draw_game()
        elif self.game_state == "game_over":
            self.draw_game_over_screen()
        
        pygame.display.flip()
    
    def run(self):
        while self.running:
            self.handle_events()
            self.update()
            self.draw()
            self.clock.tick(FPS)
        
        pygame.quit()
        sys.exit()

if __name__ == "__main__":
    game = Game()
    game.run()
